from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .import models,serializers
from activity.models import Activity
# Create your views here.

class CreateChecklistView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def get(self,request,card_id):
        card = self.get_card(card_id)
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.ChecklistSerializer(card.checklists,many=True,context={'request':request})
        return Response(serializer.data)
    def post(self,request,card_id):
        data = request.data
        card = self.get_card(card_id)
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        data['card'] =card.id
        serializer = serializers.ChecklistSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        Activity.objects.create(description=f"{request.user.profile.name} created {serializer.instance.name} in {card.name}.",user=request.user.profile,board=card.list.board,list=card.list,card=card)
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class EditChecklistView(APIView):
    def get_checklist(self,checklist_id):
        try:
            return models.Checklist.objects.get(id=checklist_id)
        except:
            raise Http404
    def delete(self,request,checklist_id):
        checklist=self.get_checklist(checklist_id)
        if not (request.user.profile in checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        checklist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    def put(self,request,checklist_id):
        checklist=self.get_checklist(checklist_id)
        if not (request.user.profile in checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.ChecklistSerializer(checklist)
        data=request.data
        serializer.update(instance=checklist,validated_data=data)
        return Response({"detail": "Checklist edited successfully"},status=status.HTTP_200_OK)
        
class CreateTaskView(APIView):
    def get_checklist(self,checklist_id):
        try:
            return models.Checklist.objects.get(id=checklist_id)
        except:
            raise Http404
    def get(self,request,checklist_id):
        checklist = self.get_checklist(checklist_id)
        if not (request.user.profile in checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.TaskSerializer(checklist.tasks,many=True,context={"request":request})
        return Response(serializer.data)

    def post(self,request,checklist_id):
        data=request.data
        checklist=self.get_checklist(checklist_id)
        if not (request.user.profile in checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        data['checklist'] = checklist.id
        serializer = serializers.TaskSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class TaskActionsView(APIView):
    def get_task(self,task_id):
        try:
            return models.Task.objects.get(id=task_id)
        except:
            raise Http404
    def get(self,request,task_id):
        task = self.get_task(task_id)
        if not (request.user.profile in task.checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.TaskSerializer(task,context={"request":request})
        return Response(serializer.data)

    def patch(self,request,task_id):
        task = self.get_task(task_id)
        if not (request.user.profile in task.checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if task.completed:
            task.completed = False
            Activity.objects.create(description=f"{request.user.profile.name} marked {task.name} as imcomplete in {card.name}.",user=request.user.profile,board=task.checklist.card.list.board,list=task.checklist.card.list,card=task.checklist.card)
        else:
            task.completed=True
            Activity.objects.create(description=f"{request.user.profile.name} completed {task.name} in {card.name}.",user=request.user.profile,board=task.checklist.card.list.board,list=task.checklist.card.list,card=task.checklist.card)
        task.save()
        return Response(status=status.HTTP_200_OK)

    def put(self,request,task_id):
        task=self.get_task(task_id)
        if not (request.user.profile in task.checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.TaskSerializer(task)
        data=request.data
        serializer.update(instance=task,validated_data=data)
        return Response({"detail": "task edited successfully","task": serializer.data},status=status.HTTP_200_OK)

    def delete(self,request,task_id):
        task = self.get_task(task_id)
        if not (request.user.profile in task.checklist.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        Activity.objects.create(description=f"{request.user.profile.name} deleted {task.name} in {card.name}.",user=request.user.profile,board=task.checklist.card.list.board,list=task.checklist.card.list,card=task.checklist.card)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
