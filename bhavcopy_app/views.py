import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.db.models import Count, Value, Case, When, CharField
from django.shortcuts import render
from bhavcopy_app.reload_script import reload_data_for_date
import calendar

from bhavcopy_app import models

logger = logging.getLogger(__name__)

def index(request):
    """Render the index.html template."""
    return render(request, 'index.html')

def get_data(request):
    try:
        # Get query parameters
        page = int(request.GET.get("page", 1))
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        status = request.GET.get("status", "All")
        sgmt = request.GET.get("sgmt", "All")
        src = request.GET.get("src", "All")

        logger.debug(f"Request parameters - page: {page}, start_date: {start_date}, end_date: {end_date}, status: {status}, sgmt: {sgmt}, src: {src}")

        # Parse date range
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date and start_date != "null" else (datetime.today() - timedelta(days=30)).date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date and end_date != "null" else datetime.today().date()

        logger.debug(f"Parsed date range - start_date: {start_date}, end_date: {end_date}")

        # Date range
        date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

        # Filter segments and sources
        segments = ["CM", "FO", "CD"] if sgmt == "All" else [sgmt]
        sources = ["NSE", "BSE"] if src == "All" else [src]

        # Fetch data from the database
        db_results = fetch_database_results(start_date, end_date, segments, sources)

        final_results = []
        seen_records = set()  # To track unique records

        # Apply status filter
        if status == "Success":
            # Only include records with status "Success"
            filtered_results = [record for record in db_results if record["RecordCount"] > 0]
            for record in filtered_results:
                record["Weekday"] = calendar.day_name[record["TradDt"].weekday()]
                final_results.append(record)
        elif status == "Failed/Not Present":
            # Include default records for missing data
            for date in date_range:
                for segment in segments:
                    for source in sources:
                        record_key = (date, segment, source)
                        if not any(record["TradDt"] == date and record["Sgmt"] == segment and record["Src"] == source for record in db_results):
                            final_results.append({
                                "TradDt": date,
                                "Weekday": calendar.day_name[date.weekday()],
                                "Sgmt": segment,
                                "Src": source,
                                "RecordCount": 0,
                                "Status": "Failed/Not Present"
                            })
        else:  # Status == "All"
            # Include both database records and missing data
            for date in date_range:
                for segment in segments:
                    for source in sources:
                        matching_record = next((record for record in db_results if record["TradDt"] == date and record["Sgmt"] == segment and record["Src"] == source), None)
                        if matching_record:
                            matching_record["Weekday"] = calendar.day_name[matching_record["TradDt"].weekday()]
                            final_results.append(matching_record)
                        else:
                            final_results.append({
                                "TradDt": date,
                                "Weekday": calendar.day_name[date.weekday()],
                                "Sgmt": segment,
                                "Src": source,
                                "RecordCount": 0,
                                "Status": "Failed/Not Present"
                            })

        # Pagination
        items_per_page = 10
        total_pages = (len(final_results) + items_per_page - 1) // items_per_page
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        paginated_results = final_results[start_index:end_index]

        # Adjust response data for pagination
        response_data = {
            "current_page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "results": paginated_results,
        }

        return JsonResponse(response_data, safe=False)

    except Exception as e:
        logger.error(f"Error in get_data: {e}", exc_info=True)
        return JsonResponse({"error": "An error occurred while fetching data."}, status=500)


def fetch_database_results(start_date, end_date, segments, sources):
    """
    Fetch records from the database for the given date range, segments, and sources.

    Args:
        start_date (date): Start date of the range.
        end_date (date): End date of the range.
        segments (list): List of segments to filter (e.g., ['CM', 'FO']).
        sources (list): List of sources to filter (e.g., ['NSE', 'BSE']).

    Returns:
        list: A list of dictionaries containing the query results.
    """
    from django.db.models import Case, When, Value, CharField, Count

    try:
        # Query with annotations
        query = (
            models.BhavCopy.objects.filter(
                TradDt__range=(start_date, end_date),
                Sgmt__in=segments,
                Src__in=sources,
            )
            .values("TradDt", "Sgmt", "Src")
            .annotate(
                RecordCount=Count("id"),
                Status=Case(
                    When(RecordCount__gt=0, then=Value("Success")),
                    default=Value("Failed/Not Present"),
                    output_field=CharField(),
                )
            )
        )

        results = list(query)
        logger.debug(f"Database Results: {results}")
        return results

    except Exception as e:
        logger.error(f"Error in fetch_database_results: {e}", exc_info=True)
        return []


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
