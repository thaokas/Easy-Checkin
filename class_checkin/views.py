import json

import cv2
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view

from EasyCheckin.settings import FACE_EMBEDDING, VECTOR_DB_CLIENT, VECTOR_DB_NAME
from class_checkin.models import Enrollment, Student, Course


@api_view(['GET'])
def index(request):
    a = 1
    b = 2
    c = 3
    return JsonResponse({'a': a, 'b': b, 'c': c})


@api_view(['POST'])
def checkin_result(request):
    request_result = "SUCCESS"
    request_message = "CHECKIN SUCCESS"

    binary_img = request.FILES.get('checkinImg')
    course_id = int(request.POST.get('courseId'))
    course_name = request.POST.get('courseName')

    if len(Course.objects.filter(course_id=course_id)) == 0:
        request_result = "FAILED"
        request_message = "Course Id does not exist"
        return JsonResponse({'request_result': request_result, 'request_message': request_message})

    if len(Course.objects.filter(course_id=course_id, course_name=course_name)) == 0:
        request_result = "FAILED"
        request_message = "Course Id does not match Course Name"
        return JsonResponse({'request_result': request_result, 'request_message': request_message})

    course = Course.objects.get(course_id=course_id)
    query_res = Enrollment.objects.filter(Course_Id=course.id)
    student_uid_set = set([item.Student_Id.std_uid for item in query_res])

    cv2_img = cv2.imdecode(np.array(bytearray(binary_img.read()), dtype=np.byte), cv2.IMREAD_COLOR)

    feature_vectors = [face.normed_embedding for face in FACE_EMBEDDING.get(cv2_img)]

    res = VECTOR_DB_CLIENT.search(
        collection_name=VECTOR_DB_NAME,
        data=feature_vectors,
        limit=2,
        output_fields=["uid", "pk_id"]
    )

    try:
        attendance_uid_set = set([i[0]['entity']['uid'] for i in res])  # if i[0]['distance'] > 0.9])
    except IndexError:
        request_result = "FAILED"
        request_message = "No Face Exist In This Picture"
        return JsonResponse({'request_result': request_result, 'request_message': request_message})

    common_attendance_uid_set = student_uid_set.intersection(attendance_uid_set)

    absent_uid_set = student_uid_set - common_attendance_uid_set
    unknown_uid_set = attendance_uid_set - common_attendance_uid_set

    try:
        absent_students_list = [json.dumps({"name": stu.std_name, "uid": stu.std_uid}, ensure_ascii=False) for stu in Student.objects.filter(std_uid__in=absent_uid_set)]
    except IndexError:
        absent_students_list = []

    try:
        unknown_students_list = [json.dumps({"name": stu.std_name, "uid": stu.std_uid}, ensure_ascii=False) for stu in Student.objects.filter(std_uid__in=unknown_uid_set)]
    except IndexError:
        unknown_students_list = []

    all_attendance_num = len(attendance_uid_set)
    attendance_num = len(common_attendance_uid_set)
    unknown_num = len(unknown_uid_set)
    absent_num = len(absent_uid_set)

    context = {
        'request_result': request_result,
        'request_message': request_message,
        'all_attendance_num': all_attendance_num,
        'attendance_num': attendance_num,
        'unknown_num': unknown_num,
        'absent_num': absent_num,
        'absent_students_list': absent_students_list,
        'unknown_students_list': unknown_students_list,
    }

    return JsonResponse(context)
