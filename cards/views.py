from django.db.models import Q,F
from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from trello.emailfunc import send_email_to_object_watchers,send_email_to
from .import models,serializers
from lists.models import List
from boards.models import Preference
from boards.permissions import is_allowed_to_watch_or_star
# Create your views here.

class CreateCardView(APIView):
    def get_list(self,request,list_id):
        try:
            return List.objects.get(id=list_id)
        except:
            raise Http404
    def get(self, request,list_id):
        list=self.get_list(request,list_id)
        if not (request.user.profile in list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.CardSerializer(list.cards,many=True,context={'request':request})
        return Response(serializer.data)

    def post(self, request,list_id):
        data = request.data
        list=self.get_list(request,list_id)
        if not (request.user.profile in list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        data["list"] = list.id
        data['members'] = None
        data['index'] = list.cards.count()
        serializer = serializers.CardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        mail_body = f"{request.user.profile.name} created a card {data['name']} in list {list.name} in board {list.board.name}."
        mail_subject = f"{list.board.name}(Board)"
        send_email_to_object_watchers(list.board,mail_body, mail_subject)
        mail_subject = f"{list.name}(List)"
        send_email_to_object_watchers(list,mail_body, mail_subject)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class WatchUnwatchCard(APIView):
    def put(self,request,card_id):
        try:
            card = models.Card.objects.get(id=card_id)
        except:
            raise Http404
        if not is_allowed_to_watch_or_star(request,card.list.board):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if request.user.profile in card.list.board.watched_by.all():
            return Response({"detail": "You are already watching board so no need to watch card."},status=status.HTTP_400_BAD_REQUEST)
        if request.user.profile in card.list.watched_by.all():
            return Response({"detail": "You are already watching the list so no need to watch card."},status=status.HTTP_400_BAD_REQUEST)
        if request.user.profile in card.watched_by.all():
            card.watched_by.remove(request.user.profile)
            return Response({'detail' : "not watching card" })
        else:
            card.watched_by.add(request.user.profile)
            return Response({'detail': 'watching card'})



class EditCardView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def put(self,request,card_id):
        data = request.data
        card = self.get_card(card_id)
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        mail_body = f"{request.user.profile.name} edited the card {card.name} in list {card.list.name} in board {card.list.board.name}."
        if 'list' in data:
            try:
                list = List.objects.get(id=data['list'])
                data['list'] = list
            except:
                raise Http404
            if not (request.user.profile in list.board.members.all()):
                return Response(status=status.HTTP_403_FORBIDDEN)
            if not (list in card.list.board.lists.all()):
                return Response({"detail" : "Can't move card outside the board"},status=status.HTTP_403_FORBIDDEN)
            if list == card.list:
                if 'index' in data:
                    if data['index'] > card.list.cards.count()+1 or data['index']<0:
                        return Reponse({"detail": "Index can't hold this value"},status=status.HTTP_400_BAD_REQUEST)
                    if card.index > data['index']:
                        card.list.cards.filter(index__gte=data['index'],index__lt=card.index).update(index=F('index')+1)
                    else:
                        card.list.cards.filter(index__gt=card.index,index__lte=data['index']).update(index=F('index')-1)
            else:
                if 'index' in data:
                    if data['index'] > list.cards.count()+1 or data['index']<0:
                        return Reponse({"detail": "Index can't hold this value"},status=status.HTTP_400_BAD_REQUEST)
                    list.cards.filter(index__gte=data['index']).update(index=F('index')+1)
                    card.list.cards.filter(index_gt=card.index).update(index=F('index')-1)
                    mail_body = f"{request.user.profile.name} moved card {card.name} from list {card.list.name} to list {list.name}."
        send_email_to_object_watchers(card.list.board,mail_body,f"{card.list.board.name}(Board)")
        send_email_to_object_watchers(card.list,mail_body,f"{card.list.name}(List)")
        send_email_to_object_watchers(card,mail_body,f"{card.name}(Card)")
        serializer = serializers.CardSerializer(card)
        serializer.update(instance=card,validated_data=data)
        return Response({"detail": "card edited successfully"},status=status.HTTP_200_OK)


class CommentView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        board = card.list.board
        if board.preference.pref_comment == Preference.comments.disabled:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_comment == Preference.comments.admins:
            if not (request.user.profile in board.admins.all()):
                return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_comment == Preference.comments.members:
            if not (request.user.profile in board.members.all()):
                return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_comment == Preference.comments.team_members:
            if board.team:
                if not (request.user.profile in board.team.members.all()):
                    return Response(status=status.HTTP_403_FORBIDDEN)
        data = request.data
        data['card'] = card.id
        data['user'] = request.user.profile.id
        serializer = serializers.CommentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    # def is_allowed(self,request,board):
    #     if board.preference.permission_level == Preference.permission.public or request.user.profile in board.members.all():
    #         return True
    #     if board.preference.permission_level == Preference.permission.team_members:
    #         if request.user.profile in board.team.members.all():
    #             return True
    #         return False
    #     return False

    def get(self,request,card_id):
        card = self.get_card(card_id)
        board = card.list.board
        if not is_allowed_to_watch_or_star(request,board):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.CommentSerializer(card.comments,many=True,context={'request':request})
        return Response(serializer.data)

class VoteCardView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        board = card.list.board
        if board.preference.pref_voting == Preference.voting.disabled:
                return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_voting == Preference.voting.admins:
            if not (request.user.profile in board.admins.all()):
                return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_voting == Preference.voting.members:
            if not (request.user.profile in board.members.all()):
                return Response(status=status.HTTP_403_FORBIDDEN)
        if board.preference.pref_voting == Preference.voting.team_members:
            if board.team:
                if not (request.user.profile in board.team.members.all()):
                    return Response(status=status.HTTP_403_FORBIDDEN)
        if request.user.profile in card.voted_by.all():
            card.voted_by.remove(request.user.profile)
            return Response("voted card")
        else:
            card.voted_by.add(request.user.profile)
            return Response('unvoted card')
        

class CreateLabelView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        data = request.data
        data['card'] = card.id
        serializer = serializers.LabelSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class EditMembersInCard(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        members = request.data['members']
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        for member in members:
            try:
                user = card.list.board.members.get(user__email=member)
            except:
                continue
            card.members.add(user)
            if user != request.user.profile:
                mail_body = f"{request.user.profile.name} added you to card {card.name}."
                mail_subject = f'You were added to a card'
                send_email_to(member,mail_body,mail_subject) #email notification
        return Response({"detail":"successfully added members in card."})
    def put(self,request,card_id):
        card = self.get_card(card_id)
        members = request.data['members']
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        for member in members:
            try:
                user = card.members.get(user__email=member)
            except:
                continue
            card.members.remove(user)
            if user != request.user.profile:
                mail_body = f"{request.user.profile.name} removed you from the card {card.name}."
                mail_subject = f'You were removed from a card'
                send_email_to(member,mail_body,mail_subject) #email notification
        return Response({"detail":"successfully removed members from card."})

class AttachLinkView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        attachment = request.data
        attachment['card'] = card.id
        serializer = serializers.AttachedLinkSerializer(data=attachment)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class AttachFileView(APIView):
    def get_card(self,card_id):
        try:
            return models.Card.objects.get(id=card_id)
        except:
            raise Http404
    def post(self,request,card_id):
        card = self.get_card(card_id)
        if not (request.user.profile in card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        attachment = request.data
        attachment['card'] = card.id
        serializer = serializers.AttachedFileSerializer(data=attachment,context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class EditDeleteAttachedLinkView(APIView):
    def get_attachment(self,id):
        try:
            return models.Attached_link.objects.get(id=id)
        except:
            raise Http404
    def put(self,request,id):
        attachment = self.get_attachment(id)
        if not (request.user.profile in attachment.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.AttachedLinkSerializer(attachment)
        data=request.data
        serializer.update(instance=attachment,validated_data=data)
        return Response({"detail":"successful"})
    def delete(self,request,id):
        attachment = self.get_attachment(id)
        if not (request.user.profile in attachment.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EditDeleteAttachedFileView(APIView):
    def get_attachment(self,id):
        try:
            return models.Attached_file.objects.get(id=id)
        except:
            raise Http404
    def put(self,request,id):
        attachment = self.get_attachment(id)
        if not (request.user.profile in attachment.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.AttachedFileSerializer(attachment)
        data=request.data
        serializer.update(instance=attachment,validated_data=data)
        return Response({"detail":"successful"})
    def delete(self,request,id):
        attachment = self.get_attachment(id)
        if not (request.user.profile in attachment.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EditDeleteLabelView(APIView):
    def get_label(self,id):
        try:
            return models.Label.objects.get(id=id)
        except:
            raise Http404
    def put(self,request,id):
        label = self.get_label(id)
        if not (request.user.profile in label.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = serializers.LabelSerializer(label)
        data=request.data
        serializer.update(instance=label,validated_data=data)
        return Response({"detail":"successful"})
    def delete(self,request,id):
        label = self.get_label(id)
        if not (request.user.profile in label.card.list.board.members.all()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        label.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)