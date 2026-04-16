from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Note
from .serializers import NoteSerializer


class NoteListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notes = Note.objects.filter(user=request.user)
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NoteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_note(self, request, pk):
        try:
            return Note.objects.get(pk=pk, user=request.user)
        except Note.DoesNotExist:
            return None

    def get(self, request, pk):
        note = self.get_note(request, pk)
        if not note:
            return Response(
                {'error': 'Note not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(NoteSerializer(note).data)

    def patch(self, request, pk):
        note = self.get_note(request, pk)
        if not note:
            return Response(
                {'error': 'Note not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = NoteSerializer(note, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        note = self.get_note(request, pk)
        if not note:
            return Response(
                {'error': 'Note not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
