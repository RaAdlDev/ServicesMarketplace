from sqlalchemy.orm import Session
from sqlalchemy import select
from schemas.abilities import AbilitiesInput
from models.abilitie import Abilitie

def post_abilitie(db: Session, abilitie_data: AbilitiesInput):
    verify_unique = db.execute(select(Abilitie).where(Abilitie.name == abilitie_data.name)).scalar_one_or_none()
    if verify_unique:
        return None
    new_abilitie = Abilitie(
        name = abilitie_data.name
    )
    db.add(new_abilitie)
    db.commit()
    db.refresh(new_abilitie)

    return new_abilitie

def view_abilities(db: Session):
    return db.execute(select(Abilitie)).scalars().all()