import logging

from rest_framework import status
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None or response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        view = context.get("view")
        view_name = view.__class__.__name__ if view else "unknown view"
        logger.error(
            "Unhandled API exception in %s",
            view_name,
            exc_info=(type(exc), exc, exc.__traceback__),
        )

    if response is None:
        return Response(
            {"detail": "An unexpected error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response