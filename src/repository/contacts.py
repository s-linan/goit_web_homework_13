from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, or_, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdate


async def search_contacts_by(db: AsyncSession, first_name: Optional[str] = None,
                             last_name: Optional[str] = None,
                             email: Optional[str] = None):
    stmt = select(Contact).filter(
        or_(Contact.first_name == first_name, Contact.last_name == last_name, Contact.email == email))
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contacts_with_birthdays(limit: int, db: AsyncSession):
    current_date = datetime.now().date()
    end_date = current_date + timedelta(days=limit)

    search = select(Contact).filter(
        or_(
            and_(
                extract('month', Contact.birthday) == current_date.month,
                extract('day', Contact.birthday) >= current_date.day
            ),
            and_(
                extract('month', Contact.birthday) == end_date.month,
                extract('day', Contact.birthday) <= end_date.day
            ),
            and_(
                extract('month', Contact.birthday) == (current_date.month + 1) % 12,
                extract('day', Contact.birthday) <= end_date.day
            )
        )
    )

    result = await db.execute(search)
    return result.scalars().all()


async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_all_contacts(limit: int, offset: int, db: AsyncSession):
    stmt = select(Contact).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()


async def create_contact(body: ContactSchema, db: AsyncSession, user: User):
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdate, db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        for key, value in body.dict(exclude_unset=True).items():
            setattr(contact, key, value)
        await db.commit()
        await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact
