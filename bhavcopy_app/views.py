import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Value
from django.db.models.functions import Coalesce
from .models import BhavCopy
from django.shortcuts import render
from django.db import models
import calendar  # Add this import

logger = logging.getLogger(__name__)

def index(request):
    """Render the index.html template."""
    return render(request, 'index.html')


def get_data(request):
    try:
        logger.debug("Received request for data.")

        # Extracting query parameters
        page = int(request.GET.get("page", 1))
        start_date = request.GET.get("start_date", None)
        end_date = request.GET.get("end_date", None)
        status = request.GET.get("status", None)
        sgmt = request.GET.get("sgmt", None)
        src = request.GET.get("src", None)

        logger.debug(f"Request parameters - page: {page}, start_date: {start_date}, end_date: {end_date}, status: {status}, sgmt: {sgmt}, src: {src}")

        # Handle null parameters by defaulting to the current month
        if not start_date or start_date == "null":
            start_date = datetime.now().date().replace(day=1)  # First day of the current month
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        if not end_date or end_date == "null":
            end_date = (datetime.now().date().replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)  # Last day of the current month
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        logger.debug(f"Parsed date range - start_date: {start_date}, end_date: {end_date}")

        # Query the database with filters
        queryset = BhavCopy.objects.filter(BizDt__range=(start_date, end_date))

        if sgmt and sgmt != "null":
            queryset = queryset.filter(Sgmt=sgmt)

        if src and src != "null":
            queryset = queryset.filter(Src=src)

        queryset = queryset.values('BizDt', 'Sgmt', 'Src').annotate(
            RecordCount=Count('FinInstrmId'),
            Status=Value('Success', output_field=models.CharField())
        )


        # Create a complete date range for the month
        date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        # Fill in missing dates
        queryset_dates = {record["BizDt"]: record for record in queryset}
        final_results = []
        for date in date_range:
            if date in queryset_dates:
                record = queryset_dates[date]
                record["Weekday"] = calendar.day_name[date.weekday()]
                final_results.append(record)
            else:
                final_results.append({
                    "BizDt": date,
                    "RecordCount": 0,
                    "Status": "Failed/Not Present",
                    "Weekday": calendar.day_name[date.weekday()]
                })

        # Paginate results
        paginator = Paginator(final_results, 10)
        results = paginator.page(page)

        return JsonResponse({
            "results": list(results),
            "current_page": results.number,
            "total_pages": paginator.num_pages,
            "has_next": results.has_next(),
            "has_previous": results.has_previous()
        })

    except Exception as e:
        logger.error(f"Error in get_data: {e}")
        return JsonResponse({"error": str(e)}, status=500)


from django.http import JsonResponse
from .reload_script import reload_data_for_date
import logging

def reload_date(request, date):
    """Reload data for a specific date."""
    try:
        # Parse sgmt and src from the request body
        body = json.loads(request.body)
        sgmt = body.get("sgmt", "CM")  # Default to CM if not provided
        src = body.get("src", "NSE")  # Default to NSE if not provided

        print(f"Reloading for Date: {date}, Segment: {sgmt}, Source: {src}")

        result = reload_data_for_date(date, sgmt, src)
        if result["success"]:
            return JsonResponse({"success": True, "message": result["message"]})
        else:
            return JsonResponse({"success": False, "error": result["error"]})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})



# Ensure proper logging setup
logging.basicConfig(level=logging.DEBUG)
