import logging

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from portfolio.infrastructure.xtb import parse_xtb_cash_operations_xlsx
from portfolio.services.transaction_import_service import import_normalized_transactions

logger = logging.getLogger(__name__)


class XtbCashOperationsImportView(APIView):
    """
    Upload an XTB multi-sheet .xlsx export; import trade rows from the Cash Operations sheet.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if not upload:
            return Response(
                {"detail": "No file provided. Use the field name 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = getattr(upload, "name", "") or ""
        if not str(name).lower().endswith(".xlsx"):
            return Response(
                {"detail": "Expected an Excel file with extension .xlsx."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            upload.seek(0)
        except (AttributeError, OSError):
            pass

        try:
            rows = parse_xtb_cash_operations_xlsx(upload)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("XTB cash operations parse failed")
            return Response(
                {"detail": "Could not read the spreadsheet. Check that it is a valid XTB export."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = import_normalized_transactions(request.user, rows)
        outcomes = [
            {
                "source_row_index": o.source_row_index,
                "status": o.status,
                "transaction_id": o.transaction_id,
                "message": o.message,
            }
            for o in result.outcomes
        ]

        return Response(
            {
                "created_count": result.created_count,
                "parsed_row_count": len(rows),
                "outcomes": outcomes,
            },
            status=status.HTTP_200_OK,
        )
