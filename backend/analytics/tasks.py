from celery import shared_task


@shared_task(bind=True, soft_time_limit=3300, time_limit=3600)
def train_sarima_forecasts(self):
    """Nightly batch: fit SARIMA per top stock and store the forecasts.
    Per-symbol failures are handled inside the batch, so no autoretry."""
    from analytics.services.forecast_service import run_sarima_batch

    return run_sarima_batch()


@shared_task(
    bind=True,
    soft_time_limit=900,
    time_limit=1200,
    autoretry_for=(Exception,),
    retry_backoff=60,
    max_retries=2,
)
def train_regression_model_task(self):
    """Nightly: retrain the shared index regression model and persist it."""
    from analytics.services.regression_model import train_and_save_regression_model

    return train_and_save_regression_model()
