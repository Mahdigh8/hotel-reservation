from datetime import date, timedelta, datetime
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Hotel, Room, Reserve
from .forms import HotelDatePickerForm



def home_page(request):
    hotel_suggestions = Hotel.objects.filter(rating__gt=3).order_by('-rating')
    hotel_suggestions = hotel_suggestions[:3]
    return render(request, 'blog/hotel/home.html', {'hotel_suggestions': hotel_suggestions})


def hotel_detail(request, id):
    hotel = get_object_or_404(Hotel, id=id)
    return render(request, 'blog/hotel/detail.html', {'hotel': hotel})


@login_required
def hotel_reserve(request, id):
    error_message = None
    if request.method == "POST":
        ### if request came from form1
        if request.POST['form_select'] == 'form1':
            form = HotelDatePickerForm(request.POST)
            if form.is_valid():
                begin = form.cleaned_data.get('begin')
                end = form.cleaned_data.get('end')
            else:
                begin = date.today()
                end = date.today() + timedelta(days=3)
                error_message = ''
        ### if request came from form2
        elif request.POST['form_select'] == 'form2':
            reserve, begin, end, error_message = make_reserve(request)
            if error_message == None:
                return HttpResponseRedirect(reverse('blog:reserve_factor', args=(reserve.trackingCode,)))
            else:
                form = HotelDatePickerForm(initial={'begin': begin, 'end':end})
    ### if GET request
    else:
        begin = date.today()
        end = date.today() + timedelta(days=3)
        form = HotelDatePickerForm(initial={'begin': begin, 'end':end})

    hotel = get_object_or_404(Hotel, id=id)
    ### if error is from form1 do not show available rooms
    avl_rooms = []
    if error_message != '':
        room_list = Room.objects.filter(hotel__id=id)
        avl_rooms = check_room(room_list, begin, end)

    return render(request, 'blog/hotel/reserve.html',
            {'hotel': hotel, 'rooms': avl_rooms,
             'error_message': error_message, 'form':form,
             'begin': begin, 'end': end})


def check_room(rl, begin, end):
    avl_rooms = []
    for i in rl:
        temp = i.reserve_set.filter(beginDate__lte=begin, endDate__gt=begin)
        if temp.first() == None:
            temp = i.reserve_set.filter(beginDate__gt=begin)
            temp = temp.filter(beginDate__lt=end)
            if temp.first() == None:
                avl_rooms.append(i)

    return avl_rooms


def make_reserve(request):
    reserve = None
    error_message = None

    selected_rooms = request.POST.getlist('selected_rooms')
    hotel_id = request.POST['hotel_id']

    ### make date objects
    begin = request.POST['begin']
    end = request.POST['end']
    begin_test = begin.split('-')
    begin = datetime(int(begin_test[0]), int(begin_test[1]), int(begin_test[2]))
    end_test = end.split('-')
    end = datetime(int(end_test[0]), int(end_test[1]), int(end_test[2]))


    if selected_rooms:
        room_list = Room.objects.filter(hotel__id=hotel_id)
        avl_rooms = check_room(room_list, begin, end)
        avl_rooms = [str(i.id) for i in avl_rooms]
        ### Check if selected rooms still available or not
        if all(elem in avl_rooms  for elem in selected_rooms):
            ### Create Reserve
            days = (end - begin).days

            total_price = 0
            room_list = []
            for room_id in selected_rooms:
                room = Room.objects.filter(id=room_id)[0]
                room_list.append(room)
                total_price += room.price
            
            total_price = total_price*days

            ### calculate discount
            hotel = get_object_or_404(Hotel, id=hotel_id)
            total_price = (total_price*(100 - hotel.discount))/100

            reserve = Reserve.objects.create(user=request.user, beginDate=begin,
                                             endDate=end, totalPrice=total_price)
            reserve.room.set(room_list)
            reserve.save()
        else:
            ### if selected rooms are not available
            error_message = "اتاق های انتخابی در دسترس نمیباشد."

    else:
        ### if no rooms were selected
        error_message = "اتاقی انتخاب نشده است."

    return reserve, begin, end, error_message


@login_required
def reserve_factor(request, tracking_code):
    reserve = get_object_or_404(Reserve, trackingCode=tracking_code)
    return render(request, 'blog/hotel/reserve_factor.html',
                 {'reserve': reserve})


"""
this view has two forms one for searching over hotel names
and another one for search hotels by their city.
"""
@require_http_methods(["GET"])
def search(request):
    show_all = False
    ### these variables will send to template as context
    hotel_list = []
    city_checked = []
    ranking_checked = []
    hotel_name = ''

    ### Which form is submitted
    ## form1 gets hotel's name
    form_select = request.GET.get('form_select')
    if form_select == 'form1':
        hotel_name = request.GET.get('hotel_name')
        ### check if there is a hotel_name or the form was empty
        if hotel_name:
            hotel_list = Hotel.objects.filter(name=hotel_name)
        else:
            ## if form is empty show all hotels
            show_all = True

    ## form2 gets selected citys and rankings
    elif form_select == 'form2':
        city_checked = request.GET.getlist('city_checked')
        ranking_checked = request.GET.getlist('ranking_checked')
        ### check if there is a checked city or the form was empty
        if city_checked:
            ### check if there is a checked ranking or not
            if not ranking_checked:
                ## for every selected cities get their hotels and add them to hotel_list
                for city in city_checked:
                    for hotel in Hotel.objects.filter(city=city):
                        hotel_list.append(hotel)
        
            else:
                ## for every selected cities get their hotels and add them to hotel_list
                for city in city_checked:
                    for hotel in Hotel.objects.filter(city=city, rating__in=ranking_checked):
                        hotel_list.append(hotel)
        else:
            ## if no city was selected show all hotels based on ranking
            if ranking_checked:
                hotel_list = Hotel.objects.filter(rating__in=ranking_checked)
            else:
                show_all = True

    else:
        ## if request is GET and we don't submit any forms then show all hotels
        show_all = True

    ### show all the hotels
    if show_all==True:
        hotel_list = Hotel.objects.all()

    ### pagination hotel_list
    paginator = Paginator(hotel_list, 3) # 3 posts in each page
    page = request.GET.get('page')
    if page == None:
        page = 1

    try:
        hotel_list = paginator.page(page)
    except PageNotAnInteger:
    # If page is not an integer deliver the first page
        hotel_list = paginator.page(1)
    except EmptyPage:
    # If page is out of range deliver last page of results
        hotel_list = paginator.page(paginator.num_pages)

    ### Get all city names
    all_hotels = Hotel.objects.all()    
    city_list = []
    for hotel in all_hotels:
        city_list.append(hotel.city)
    city_list = list(dict.fromkeys(city_list))

    ### make url for checked cities
    city_checked_url = ""
    for i in city_checked:
        city_checked_url += "&city_checked=" + i

    ranking_checked_url = ""
    for i in ranking_checked:
        ranking_checked_url += "&ranking_checked=" + i

    return render(request, 'blog/hotel/search.html',
                {'hotel_list': hotel_list, 'city_list': city_list,
                 'city_checked_url': city_checked_url,
                 'ranking_checked_url': ranking_checked_url, 'hotel_name': hotel_name})
