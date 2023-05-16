import json
from typing import Any, Dict, List, Union

from backend.app.api.dependencies.db import get_db
from backend.app.core.settings import settings
from backend.app.db.repositories.email import email_repo
from backend.app.models.email import Email
from backend.app.schemas.email import EmailCreate, EmailUpdate
from loguru import logger
from postmarker.core import PostmarkClient
from pydantic import EmailStr
from sqlalchemy.orm.session import Session

DEFAULT_EMAIL_SENDER = settings.DEFAULT_EMAIL_SENDER
POSTMARK_API_TOKEN = settings.POSTMARK_API_TOKEN


EMAIL_OK = "OK"
EMAIL_SUCCESS_ERRORCODE = 0


def is_success_response(response):
    return (
        response
        and response["Message"] == EMAIL_OK
        and response["ErrorCode"] == EMAIL_SUCCESS_ERRORCODE
    )


def send_email_with_template(
    client: PostmarkClient,
    template_id: int,
    template_dict: Dict[str, Any],
    recipient: Union[List[EmailStr], EmailStr],
):
    db: Session = next(get_db())

    email: Email = email_repo.create(
        db,
        obj_in=EmailCreate(
            template_id=template_id,
            template_dict=json.dumps(template_dict),
            recipient=recipient,
            sender=DEFAULT_EMAIL_SENDER,
        ),
    )
    return _send_email_with_template(
        client, db=db, email=email, template_dict=template_dict
    )


def _send_email_with_template(
    client: PostmarkClient, *, db: Session, email: Email, template_dict: Dict[str, Any]
):
    try:
        response = client.emails.send_with_template(
            TemplateId=email.template_id,
            TemplateModel=template_dict,
            From=DEFAULT_EMAIL_SENDER,
            To=email.recipient,
        )
        if is_success_response(response):
            email_repo.mark_as_delivered(db, db_obj=email)
        else:
            email_repo.update(
                db,
                db_obj=email,
                obj_in=EmailUpdate(delivered=False, extra_data=response["Message"]),
            )
        if settings.DEBUG:
            logger.info("***EMAIL****")
            logger.info(f"Recipient : {email.recipient}")
            logger.info(template_dict)

    except Exception as e:
        logger.error(e)
        email_repo.update(
            db,
            db_obj=email,
            obj_in=EmailUpdate(delivered=False, extra_data=e.__str__()),
        )
