from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.utils import timezone
from dateutil import parser
from datetime import date, datetime, timedelta
import json
import pytz
from .parse_database import (
    filter_events,
    get_unique_locations,
    get_events_by_hour,
    get_category_data,
)
from .generate_map import create_map, add_event_markers, generate_heatmap
from .parse_database import filter_events_by_category, get_unique_categories
from .models import Event


def home(request):
    """Render home page with search, location, date, and category filters."""
    # Get query parameters
    query = request.GET.get("query", "")
    locations = request.GET.getlist("locations")
    categories = request.GET.getlist("categories")

    # Set local time to est
    est = pytz.timezone("America/New_York")
    timezone.activate(est)

    # Calculate default start and end dates for the next week in est time
    today = timezone.now().astimezone(est).date()
    default_start_date = today
    default_end_date = today + timedelta(days=7)

    # Use user-provided dates or default values and convert to UTC for database query
    if request.GET.get("start_date"):
        start_time = parser.parse(request.GET.get("start_date"))
    else:
        start_time = default_start_date
    
    start_time = datetime(
        start_time.year, start_time.month, start_time.day, 0, 0, 0, tzinfo=pytz.timezone("America/New_York")
    )
    start_time = start_time.astimezone(pytz.UTC)
    start_date = start_time.date()
    
    if request.GET.get("end_date"):
        end_time = parser.parse(request.GET.get("end_date"))
    else:
        end_time = default_end_date
        
    end_time = datetime(
        end_time.year, end_time.month, end_time.day, 23, 59, 59, tzinfo=pytz.timezone("America/New_York")
    )
    end_time = end_time.astimezone(pytz.UTC)
    end_date = end_time.date()

    # Filter events
    events = filter_events(
        query=query,
        locations=locations,
        start_date=start_date,
        end_date=end_date,
    )
    events = filter_events_by_category(events, categories).order_by("start_time")

    return render(
        request,
        "access_amherst_algo/home.html",
        {
            "events": events,
            "query": query,
            "selected_locations": locations,
            "selected_categories": categories,
            "start_date": start_time.date().isoformat(),
            "end_date": end_time.date().isoformat(),
            "unique_locations": get_unique_locations(),
            "unique_categories": get_unique_categories(),
        },
    )


def map_view(request):
    """Render map view with event markers."""
    events = Event.objects.exclude(
        latitude__isnull=True, longitude__isnull=True
    )
    folium_map = create_map([42.37031303771378, -72.51605520950432])
    add_event_markers(folium_map, events)
    return render(
        request,
        "access_amherst_algo/map.html",
        {"map_html": folium_map._repr_html_()},
    )


def data_dashboard(request):
    """Render dashboard with event insights and heatmap."""
    est = pytz.timezone("America/New_York")

    events = Event.objects.all()

    context = {
        "events_by_hour": get_events_by_hour(events, est),
        "category_data": get_category_data(
            events.exclude(categories__isnull=True), est
        ),
        "map_html": generate_heatmap(
            events, est
        )._repr_html_(),  # Convert to HTML here
    }

    return render(request, "access_amherst_algo/dashboard.html", context)


@csrf_exempt
def update_heatmap(request):
    """Update heatmap based on selected time range from request."""
    if request.method == "POST":
        data = json.loads(request.body)
        est = pytz.timezone("America/New_York")

        folium_map = generate_heatmap(
            events=Event.objects.all(),
            timezone=est,
            min_hour=data.get("min_hour", 7),
            max_hour=data.get("max_hour", 22),
        )

        map_html = folium_map._repr_html_()  # Convert to HTML here
        return JsonResponse({"map_html": map_html})



def calendar_view(request):
    est = pytz.timezone("America/New_York")
    timezone.activate(est)
    today = timezone.now().astimezone(est).date()
    days_of_week = [(today + timedelta(days=i)) for i in range(7)]
    times = [datetime.strptime(f"{hour}:00", "%H:%M").time() for hour in range(5, 23)]

    start_date = datetime(days_of_week[0].year, days_of_week[0].month, days_of_week[0].day, 0, 0, 0, 
                          tzinfo=pytz.timezone("America/New_York")).astimezone(pytz.UTC).date()
    end_date = datetime(days_of_week[-1].year, days_of_week[-1].month, days_of_week[-1].day, 23, 59, 59,
                        tzinfo=pytz.timezone("America/New_York")).astimezone(pytz.UTC).date()
    events = filter_events(start_date=start_date, end_date=end_date)

    events_by_day = {}
    for day in days_of_week:
        events_by_day[day.strftime('%Y-%m-%d')] = []
    
    # Group events by day and calculate overlaps
    for event in events:
        start_time_est = event.start_time.astimezone(pytz.timezone("America/New_York"))
        end_time_est = event.end_time.astimezone(pytz.timezone("America/New_York"))

        event_date = start_time_est.date()
        event_date_str = event_date.strftime('%Y-%m-%d')
        if event_date_str in events_by_day:
            event_obj = {
                "title": event.title,
                "location": event.location,
                "start_time": start_time_est,
                "end_time": end_time_est,
                "top": (start_time_est.hour - 7) * 60 + start_time_est.minute,
                "height": ((end_time_est.hour - start_time_est.hour) * 60 + 
                          (end_time_est.minute - start_time_est.minute)),
                "column": 0,  # Will be set during overlap detection
                "columns": 1  # Will be set during overlap detection
            }
            events_by_day[event_date_str].append(event_obj)

    # Calculate overlaps for each day
    for day, events in events_by_day.items():
        if not events:
            continue
            
        # Sort events by start time
        events.sort(key=lambda x: x['start_time'].astimezone(pytz.timezone("America/New_York")))
        
        # Find overlapping groups
        for i, event in enumerate(events):
            overlapping = []
            for other in events:
                if event != other and is_overlapping(event, other):
                    overlapping.append(other)
            
            if overlapping:
                # Calculate total columns needed
                max_columns = len(overlapping) + 1
                taken_columns = set()
                for e in overlapping:
                    if 'column' in e:
                        taken_columns.add(e['column'])
                
                # Find first available column
                for col in range(max_columns):
                    if col not in taken_columns:
                        event['column'] = col
                        break
                
                # Update columns count for all overlapping events
                event['columns'] = max_columns
                for e in overlapping:
                    e['columns'] = max_columns

    return render(
        request,
        "access_amherst_algo/calendar.html",
        {
            "days_of_week": days_of_week,
            "times": times,
            "events_by_day": events_by_day,
        },
    )


def is_overlapping(event1, event2):
    return not (event1['end_time'] <= event2['start_time'] or 
               event2['end_time'] <= event1['start_time'])