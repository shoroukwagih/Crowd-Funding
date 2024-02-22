from django.shortcuts import render,reverse,redirect, get_object_or_404
from fundProject.models import *
from django.http import HttpResponse, HttpResponseRedirect
from datetime import datetime
from .models import Categories
from .models import Images
from .models import Rate
from django.contrib import messages
from django.http import Http404
from django.db.models import Sum
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import Project, Categories
from django.db.models import Q
from django.db.models import Avg

import re
def mainPage(request):
    return  render(request,'fundProject/home.html')


def ProjectListByCategory(request, category_id):
    categoryID = Categories.objects.get(id=category_id)
    projects = Project.objects.filter(category_id=categoryID)
    for project in projects:
        setattr(project, 'img', Images.objects.filter(project_id=project))

    context = {'projects': projects, 'categoryID': categoryID}
    context['imgs']=Images.imageList()
    return render(request, 'category/projectTheRelatedCategory.html',context )



@login_required(login_url='/user/login')
def addProject(request):
    categories = Categories.objects.all()
    if request.method == 'POST':
        project = Project.projectAdd(request)
        tags_input = request.POST.get('tag', '').strip()  
        tags = [tag.strip() for tag in re.split(r'[, ]+', tags_input) if tag.strip()]
        if tags and not tags[0]:
            del tags[0]
        
        for tag_name in tags:
            tag = Tags(project_id=project, tag_name=tag_name)
            tag.save()
        
        print('Project added', project.id)
        
        images = request.FILES.getlist('projectimage[]')
        if images:
            for img in images:
                image = Images(img=img, project_id=project)
                image.save()
        
        return HttpResponseRedirect(reverse('project.all'))
    
    return render(request, 'fundProject/addProject.html', {'categories': categories})


def projectList(request):
    projects = Project.objects.all().order_by('-startTime')[:5]
    categories = Categories.objects.all()
    
    for project in projects:
        setattr(project, 'img', Images.objects.filter(project_id=project))
        tags = Tags.objects.filter(project_id=project)
        project.tags = ",".join(tag.tag_name for tag in tags)
        if project.tags.startswith(","):
            project.tags = project.tags[1:]
        
        # Calculate the average rate for the project
        avg_rate = Rate.objects.filter(project_id=project).aggregate(Avg('rate'))
        project.avg_rate = avg_rate['rate__avg']
    
    context = {'projects': projects, "categories": categories}
    context['imgs'] = Images.imageList()
    
    return render(request, 'fundProject/home.html', context)





def formatDate(input_date):
    formatted_date = input_date.strftime('%Y-%m-%d')
    return formatted_date



@login_required(login_url='/user/login')
@transaction.atomic
def projectUpdate(request, id):
    project = Project.projectDetails(id)
    project.startTime = formatDate(project.startTime)
    project.endTime = formatDate(project.endTime)
    categories = Categories.objects.all()
    existing_tags = []
    if request.method == 'POST':
        if request.POST.get('title', '') != '':
            Project.projectUpdate(request, id)
            new_tags_input = request.POST.get('tag', '').strip()
            new_tags = [tag.strip() for tag in re.split(r'[, ]+', new_tags_input) if tag.strip()]
            project_tags = Tags.objects.filter(project_id=project)
            existing_tags = [tag.tag_name for tag in project_tags]
            for tag in project_tags:
                if tag.tag_name not in new_tags:
                    tag.delete()
            for tag_name in new_tags:
                if tag_name not in existing_tags:
                    Tags.objects.create(project_id=project, tag_name=tag_name)

            return HttpResponseRedirect(reverse('project.all'))
        else:
            context['msg'] = 'Kindly fill all fields'
    else:
        project_tags = Tags.objects.filter(project_id=project)
        existing_tags = [tag.tag_name for tag in project_tags]
    
    existing_tags_str = ",".join(existing_tags)
    context = {'project': project, 'categories': categories, 'existing_tags': existing_tags_str}
    return render(request, 'fundProject/updateProject.html', context)

@login_required(login_url='/user/login')
def projectDelete(request, id):
    project = Project.objects.get(id=id)
    total_donations = Donation.objects.filter(project_id=project).aggregate(total_donations=Sum('donation_value'))['total_donations']
    total_target_float = float(project.totalTarget)
    if total_donations is not None and total_donations > total_target_float * 0.25:
        messages.error(request, 'Cannot delete project: total donations exceed 25% of the total target.')
    else:
        Project.projectDelete(id)
        Tags.objects.filter(project_id=project).delete()
        messages.error(request, 'Success Delete Project')
    return HttpResponseRedirect(reverse('project.all'))





@login_required(login_url='/user/login')
def projectDetails(request, projectid):
    obj = Project.projectDetails(projectid)
    setattr(obj, 'img', Images.objects.filter(project_id=obj))
    last_rate = Rate.objects.filter(project_id=obj, user=request.user).first()
    sum_donate = Donation.objects.filter(project_id=obj).aggregate(Sum('donation_value'))['donation_value__sum']
    comments = Comment.objects.filter(project_id=obj)  
    project_tags = Tags.objects.filter(project_id=obj)
    similar_projects = Project.objects.filter(tags__tag_name__in=project_tags.values('tag_name')).exclude(id=obj.id).distinct()[:4]
    
    avg_rate = Rate.objects.filter(project_id=obj).aggregate(Avg('rate'))['rate__avg']
    
    for project in similar_projects:
        setattr(project, 'img', Images.objects.filter(project_id=project))
        project.tags = Tags.objects.filter(project_id=project)
    
    obj.tags = ", ".join(tag.tag_name for tag in project_tags)
    if obj.tags.startswith(","):
        obj.tags = obj.tags[1:]
    
    context = {'project': obj, 'last_rate': last_rate, 'sum_donate': sum_donate, 'comments': comments, "project_tags": project_tags, 'avg_rate': avg_rate}
    context['similar_projects'] = similar_projects
    return render(request, 'fundProject/detailProject.html', context)

@login_required(login_url='/user/login')
def comment(request, id):
    obj = Project.projectDetails(id)
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text')
        if comment_text:
            Comment.objects.create(project_id=obj, comment=comment_text,user=request.user)
    comments = Comment.objects.filter(project_id=obj)
    context = {'project': obj, 'comments': comments}
    return render(request, 'fundProject/comment.html', context)

@login_required(login_url='/user/login')
def CommentDelete(request, id, comment_id):
    obj = Project.projectDetails(id)
    comments = Comment.objects.filter(project_id=obj)
    comment = get_object_or_404(comments, pk=comment_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('comment', id=id)  
    return redirect('comment', id=id)  

@login_required(login_url='/user/login')
def add_rate(request, project_id):
    if request.method == 'GET':
        rate = request.GET.get('rate')
        if rate is not None and rate.isdigit():
            rate = int(rate)
            if 0 <= rate <= 10:  
                project = get_object_or_404(Project, pk=project_id)
                existing_rate = Rate.objects.filter(project_id=project, user=request.user).first()
                if existing_rate:
                    existing_rate.rate = rate
                    existing_rate.save()
                else:
                    Rate.objects.create(project_id=project, rate=rate, user=request.user)
                messages.success(request, 'Rate added successfully.')
            else:
                messages.error(request, 'Rate must be between 0 and 10.')
        else:
            messages.error(request, 'Rate must be a positive number.')
    return redirect('projectDetails', projectid=project_id)



@login_required(login_url='/user/login')
def add_donate(request, project_id):
    if request.method == 'GET':
        donation_value = request.GET.get('donation_value')
        if donation_value is not None and donation_value.isdigit():
            donation_value = int(donation_value)
            if donation_value > 0: 
                project = get_object_or_404(Project, pk=project_id)
                Donation.objects.create(project_id=project, donation_value=donation_value,user=request.user)
                return redirect('projectDetails', projectid=project_id)
            else:
                messages.error(request, 'Donation value must be a positive number.')
        else:
            messages.error(request, 'Invalid donation value.')
    return redirect('projectDetails', projectid=project_id)

@login_required(login_url='/user/login')
def addCategory(request):
    if request.method == 'POST':
        category_name = request.POST.get('categoryName')
        if Categories.objects.filter(categoryName=category_name).exists():
            messages.error(request, 'Category with this name already exists.')
            return redirect('addCategory')
        else:
            Categories.objects.create(categoryName=category_name)
            return redirect('allCategory') 
        Categories.objects.create(categoryName=category_name)
        return HttpResponseRedirect(reverse('allCategory'))
    categories = Categories.objects.all()
    return render(request, 'category/addCategory.html', {'categories': categories})

@login_required(login_url='/user/login')
def allCategory(request):
    categories = Categories.objects.all()
    return render(request, 'category/allCategory.html', {'categories': categories})

@login_required(login_url='/user/login')
def deleteCategory(request):
    if request.method == 'POST':
        category_id = request.POST.get('categoryToDelete')
        category = Categories.objects.get(pk=category_id)
        category.delete()
    return redirect('allCategory')

@login_required(login_url='/user/login')
def search_projects(request):
    query = request.GET.get('search')
    projects_by_title = Project.objects.filter(title__exact=query)
    projects_by_tag = Project.objects.filter(tags__tag_name__exact=query)
    projects = (projects_by_title | projects_by_tag).distinct()
    categories = Categories.objects.all()
    for project in projects:
        setattr(project, 'img', Images.objects.filter(project_id=project))
        tags = Tags.objects.filter(project_id=project)
        project.tags = ",".join(tag.tag_name for tag in tags)
        if project.tags.startswith(","):
            project.tags = project.tags[1:]
    context = {'projects': projects, 'query': query,'categories':categories}
    context['imgs']=Images.imageList()
    return render(request, 'fundProject/home.html', context)



@login_required(login_url='/user/login')
def topProjectRate(request):
    projects = Project.objects.annotate(avg_rate=Avg('rate__rate')).order_by('-avg_rate')[:5]
    
    categories = Categories.objects.all()
    
    for project in projects:
        tags = Tags.objects.filter(project_id=project)
        project.tags = ",".join(tag.tag_name for tag in tags)
        if project.tags.startswith(","):
            project.tags = project.tags[1:]
        
        project.img = Images.objects.filter(project_id=project)
    
    context = {
        'projects': projects,
        "categories": categories,
        'imgs': Images.imageList()  
    }
    
    return render(request, 'fundProject/home.html', context)
    
