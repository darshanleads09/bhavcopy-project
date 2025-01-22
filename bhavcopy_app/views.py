from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import BhavCopy
from .reload_script import reload_data_for_date
from django.shortcuts import render
from django.db.models import Count
from django.core.paginator import Paginator


def index(request):
    """Render the index.html template."""
    return render(request, 'index.html')


def get_data(request):
    page = int(request.GET.get('page', 1))
    date_filter = request.GET.get('date', None)

    # Filter data by date if provided
    queryset = BhavCopy.objects.values('BizDt').annotate(
        RecordCount=Count('FinInstrmId')  # Use FinInstrmId instead of id
    ).order_by('-BizDt')

    if date_filter:
        queryset = queryset.filter(BizDt=date_filter)

    # Pagination logic
    per_page = 10
    total_records = queryset.count()
    total_pages = (total_records + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page

    data = list(queryset[start:end])
    for row in data:
        row['Status'] = 'Success' if row['RecordCount'] > 0 else 'Failed/Not Present'

    return JsonResponse({
        "results": data,
        "current_page": page,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages
    })


def reload_date(request, date):
    try:
        # Check if records exist for the date
        bhav_copies = BhavCopy.objects.filter(BizDt=date)

        if bhav_copies.exists():
            return JsonResponse({"success": True, "message": f"Data for {date} already exists!"})

        # Perform reload logic here (e.g., download and insert records)
        # Assuming a function `reload_data_from_nse` does this
        success = reload_data_for_date(date)

        if success:
            return JsonResponse({"success": True, "message": f"Data for {date} reloaded successfully!"})
        else:
            return JsonResponse({"success": False, "error": "Failed to reload data from NSE."})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

