from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission, Lesson
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
         # Get user and course object, then get the associated enrollment object created when the user enrolled the course
         # Create a submission object referring to the enrollment
         # Collect the selected choices from exam form
         # Add each selected choice object to the submission object
         # Redirect to show_exam_result with the submission id
def submit(request, course_id, lesson_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    my_lesson = get_object_or_404(Lesson, pk=lesson_id)
    my_enrollment = Enrollment.objects.filter(user=user, course=course)
    my_answers = extract_answers(request)
    
    print("Hello from submit function! Answers: {}\n".format(my_answers))
    
    submission = Submission.objects.create(enrollment=my_enrollment[0],lesson=my_lesson)
    submission.choices.set(my_answers)
    submission.save()
    
    print("My submission: {}\n".format(submission))
    print("My course id is {} and submission_id is {}\n".format(course_id,submission.id))

    return HttpResponseRedirect(reverse(viewname='onlinecourse:result', args=(course_id,lesson_id,submission.id,)))

# <HINT> A example method to collect the selected choices from the exam form from the request object
def extract_answers(request):
    submitted_anwsers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_anwsers.append(choice_id)
    return submitted_anwsers


# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
        # Get course and submission based on their ids
        # Get the selected choice ids from the submission record
        # For each selected choice, check if it is a correct answer or not
        # Calculate the total score
class SubmissionView(generic.DetailView):
    template_name = 'onlinecourse/exam_result_bootstrap.html'
    model = Submission

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        print("Get Context Data Called: {}\n".format(self.__dict__))
        print("My Enrollment: {}\n".format(self.object.enrollment))
        print("My Course: {}\n".format(self.object.enrollment.course))
        print("My User: {}\n".format(self.object.enrollment.user))

        print("Choice count: {}\n".format(self.object.choices.count()))
        my_choices = []
        for c in self.object.choices.all():
            my_choices.append(c.id)
        print("Choice ID List: {}\n".format(my_choices))


        context["course"] = self.object.enrollment.course
        context["user"] = self.object.enrollment.user

        print("My Lesson: {}\n".format(self.object.lesson))
        context["lesson"] = self.object.lesson
        my_questions = Question.objects.filter(lesson=self.object.lesson)

        print("My questions: {}\n".format(my_questions))
        context["questions"] = my_questions
        grades = []
        points_total = 0
        points_earned = 0
        for q in my_questions.all():
            print("Question: {}\n".format(q))
            correct = q.is_get_score(my_choices)
            points_total += q.grade
            if (correct):
                grades.append("{} point(s) earned (out of {})".format(q.grade,q.grade))
                points_earned += q.grade
            else:
                grades.append("0 point(s) earned (out of {})".format(q.grade))

        print("Grades: {}\n".format(grades))

        context["grades"] = grades
        context["grade"] = 100*points_earned/points_total if (points_total>0) else None

        return context



    

   





