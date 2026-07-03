from django.core.management.base import BaseCommand

from analytics.services.forecast_service import run_sarima_batch
from analytics.services.regression_model import train_and_save_regression_model


class Command(BaseCommand):
    help = (
        "Train forecasting models synchronously (no Celery broker needed). "
        "Use for initial bootstrap or debugging; nightly runs go through Celery beat."
    )

    def add_arguments(self, parser):
        parser.add_argument("--sarima", action="store_true", help="Run the SARIMA forecast batch")
        parser.add_argument("--regression", action="store_true", help="Train the shared regression model")
        parser.add_argument("--all", action="store_true", help="Run both (default when no flag given)")
        parser.add_argument(
            "--symbols",
            type=str,
            default=None,
            help="Comma-separated symbol subset for the SARIMA batch (default: top-stocks list)",
        )

    def handle(self, *args, **options):
        run_sarima = options["sarima"] or options["all"]
        run_regression = options["regression"] or options["all"]
        if not run_sarima and not run_regression:
            run_sarima = run_regression = True

        if run_sarima:
            symbols = None
            if options["symbols"]:
                symbols = [s.strip().upper() for s in options["symbols"].split(",") if s.strip()]
            result = run_sarima_batch(symbols)
            self.stdout.write(self.style.SUCCESS(
                f"SARIMA batch: {len(result['succeeded'])} succeeded, {len(result['failed'])} failed"
            ))
            for symbol, error in result["failed"].items():
                self.stdout.write(self.style.WARNING(f"  {symbol}: {error}"))

        if run_regression:
            meta = train_and_save_regression_model()
            self.stdout.write(self.style.SUCCESS(
                f"Regression model trained on {meta['symbol']} "
                f"({meta['n_samples']} samples) -> {meta['path']}"
            ))
