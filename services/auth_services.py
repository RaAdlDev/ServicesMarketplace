from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from schemas.user import UserRegister, UserLogin
from models.user import User
from core.security import hash_password, verify_password, return_token
from schemas.token import TokenResponse
import stripe
from core.settings import settings
from models.profile import Profile

stripe.api_key = settings.stripe_secret_key

def register_user(db: Session, user_data: UserRegister):
    role = user_data.role
    verify_admin = db.execute(select(User)).first()
    if not verify_admin:
        role = "ADMIN"
    verify_username_email = db.execute(select(User).where(or_(
        User.username == user_data.username,
        User.email == user_data.email
    ))).scalars().all()
    if verify_username_email:
        return None
    if role == "PROFESSIONAL":
        try:
            stripe_account = stripe.Account.create(
                type="express",
                email=user_data.email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
            )
            stripe_connect_id = stripe_account.id

            new_seller = User(
                username = user_data.username,
                email = user_data.email,
                role = role,
                hashed_password = hash_password(user_data.password),
                stripe_connect_id = stripe_connect_id,
                profile = Profile()
                )
            db.add(new_seller)
           

            link = stripe.AccountLink.create(
                account=stripe_connect_id,
                return_url="http://127.0.0.1:8000/health",
                refresh_url="http://127.0.0.1:8000/health",
                type="account_onboarding"
            )
            db.commit()

            return{
                "status": "successful request",
                "stripe_connect_id": stripe_connect_id,
                "stripe_url": link.url
            }
        
        except stripe.StripeError:
            db.rollback()
            return "STRIPE_ERROR"
        except Exception:
            db.rollback()
            return "INTERNAL_SERVER_ERROR"
        
    new_user = User(
        username = user_data.username,
        email = user_data.email,
        role = role,
        hashed_password = hash_password(user_data.password),
        profile = Profile()
    )


    db.add(new_user)
    db.commit()
    return {"status": "successful request"}

def login_user(db: Session, user_data: UserLogin):
    user = db.execute(select(User).where(User.email == user_data.email)).scalar_one_or_none()
    if not user: 
        return None
    if verify_password(user_data.password, user.hashed_password):
        return TokenResponse(token= return_token({"sub": user.user_id}), token_type="bearer")
    return None
    