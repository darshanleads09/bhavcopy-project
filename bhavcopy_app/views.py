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
from django.db import connection

logger = logging.getLogger(__name__)

def index(request):
    """Render the index.html template."""
    return render(request, 'index.html')

import json
import calendar
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.db import connection

import json
import calendar
import logging  # Import logging module
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.db import connection

# Configure logging
logger = logging.getLogger(__name__)

import json
import calendar
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.db import connection

# Configure logging
logger = logging.getLogger(__name__)

def get_data(request):
    try:
        page = int(request.GET.get("page", 1))
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        status_filter = request.GET.get("status")
        sgmt_filter = request.GET.get("sgmt")
        src_filter = request.GET.get("src")

        today = datetime.today().date()

        # Convert "null" string values to None
        if start_date in [None, "", "null"]:
            start_date = today.replace(day=1)  # Default: First day of the month
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        if end_date in [None, "", "null"]:
            end_date = today  # Default: Today's date
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

        # Prepare SQL query based on filters
        query = """
            SELECT BizDt, Sgmt, Src, COUNT(*) AS RecordCount
            FROM BhavCopy
            WHERE BizDt BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        if sgmt_filter and sgmt_filter not in ["All", "null"]:
            query += " AND Sgmt = %s"
            params.append(sgmt_filter)

        if src_filter and src_filter not in ["All", "null"]:
            query += " AND Src = %s"
            params.append(src_filter)

        query += " GROUP BY BizDt, Sgmt, Src ORDER BY BizDt DESC"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            records = cursor.fetchall()

        # Convert records to dictionary
        record_dict = {(str(row[0]), row[1], row[2]): row[3] for row in records}

        final_results = []
        segments = ["CM", "FO", "CD"] if sgmt_filter in ["All", "null", None] else [sgmt_filter]
        sources = ["NSE"] if src_filter in ["All", "null", None] else [src_filter]

        for date in date_range:
            for sgmt in segments:
                for src in sources:
                    key = (str(date), sgmt, src)
                    if key in record_dict:
                        final_results.append({
                            "BizDt": date,
                            "Sgmt": sgmt,
                            "Src": src,
                            "RecordCount": record_dict[key],
                            "Status": "Success",
                            "Weekday": calendar.day_name[date.weekday()]
                        })
                    elif status_filter in ["Failed/Not Present", "All", "null"]:
                        final_results.append({
                            "BizDt": date,
                            "Sgmt": sgmt,
                            "Src": src,
                            "RecordCount": 0,
                            "Status": "Failed/Not Present",
                            "Weekday": calendar.day_name[date.weekday()]
                        })

        # Pagination logic
        results_per_page = 10
        total_pages = (len(final_results) + results_per_page - 1) // results_per_page
        has_previous = page > 1
        has_next = page < total_pages

        paginated_results = final_results[(page - 1) * results_per_page: page * results_per_page]

        return JsonResponse({
            "results": paginated_results,
            "current_page": page,
            "total_pages": total_pages,
            "has_previous": has_previous,
            "has_next": has_next
        })

    except Exception as e:
        logger.error(f"Error in get_data: {e}", exc_info=True)  # Log error with traceback
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
