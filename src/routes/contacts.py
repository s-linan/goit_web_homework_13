from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.entity.models import User, Role
from src.services.auth import auth_service
from src.database.db import get_db
from src.repository import contacts as repositories_contacts
from src.schemas.contact import ContactSchema, ContactUpdate, ContactResponse
from src.services.roles import RoleAccess

router = APIRouter(prefix='/contacts', tags=['contacts'])
access_to_route_all = RoleAccess([Role.admin, Role.moderator])


@router.get("/search", response_model=List[ContactResponse], dependencies=[Depends(RateLimiter(times=1, seconds=5))])
async def search_contacts_by(first_name: Optional[str] = Query(None),
                             last_name: Optional[str] = Query(None),
                             email: Optional[str] = Query(None),
                             db: AsyncSession = Depends(get_db)):
    if not any([first_name, last_name, email]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="At least one of 'first_name', 'last_name' or 'email' parameters must be provided")

    contacts = await repositories_contacts.search_contacts_by(db, first_name, last_name, email)
    return contacts


@router.get("/birthdays", response_model=List[ContactResponse],
            dependencies=[Depends(RateLimiter(times=1, seconds=5))])
async def get_users_birth(limit: int = Query(7, ge=7, le=100),
                          db: AsyncSession = Depends(get_db)):
    contacts = await repositories_contacts.get_contacts_with_birthdays(limit, db)
    return contacts


@router.get("/", response_model=List[ContactResponse], dependencies=[Depends(RateLimiter(times=1, seconds=5))])
async def get_contacts(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                       db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    contacts = await repositories_contacts.get_contacts(limit, offset, db, user)
    return contacts


@router.get("/all", response_model=List[ContactResponse],
            dependencies=[Depends(access_to_route_all), Depends(RateLimiter(times=1, seconds=5))])
async def get_all_contacts(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                           db: AsyncSession = Depends(get_db),
                           user: User = Depends(auth_service.get_current_user)):
    contacts = await repositories_contacts.get_contacts(limit, offset, db, user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse, dependencies=[Depends(RateLimiter(times=1, seconds=5))])
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db),
                      user: User = Depends(auth_service.get_current_user)):
    contact = await repositories_contacts.get_contact(contact_id, db, user)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RateLimiter(times=1, seconds=5))])
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    return await repositories_contacts.create_contact(body, db, user)


@router.put("/{contact_id}")
async def update_contact(body: ContactUpdate, contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    contact = await repositories_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    contact = await repositories_contacts.delete_contact(contact_id, db, user)
    return contact
