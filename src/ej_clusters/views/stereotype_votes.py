from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, DeleteView, UpdateView
from ej.decorators import can_edit_conversation
from ej_clusters.stereotypes_utils import stereotype_vote_information
from ej_conversations.models import Conversation

from .. import forms
from ..models import Stereotype
from ..models import StereotypeVote


@method_decorator([login_required, can_edit_conversation], name="dispatch")
class StereotypeVotesView(ListView):
    template_name = "ej_clusters/stereotype-votes.jinja2"

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        conversation_id = kwargs["conversation_id"]
        self.conversation = get_object_or_404(Conversation, id=conversation_id)
        self.clusterization = self.conversation.get_clusterization(default=None)

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if self.clusterization is None:
            return render(
                request,
                self.template_name,
                {
                    "conversation": self.conversation,
                    "groups": None,
                    "current_page": "stereotypes",
                },
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.stereotype = self.clusterization.stereotypes.first()

        if "stereotype-select" in request.GET:
            self.stereotype = Stereotype.objects.get(id=request.GET["stereotype-select"])

        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        conversation = Conversation.objects.get(id=self.kwargs["conversation_id"])
        groups = self.clusterization.get_stereotypes()
        form = forms.StereotypeForm(owner=self.request.user)
        if groups:
            form = forms.StereotypeForm(instance=self.stereotype)

        return {
            "conversation": conversation,
            "stereotype": stereotype_vote_information(
                self.stereotype, self.clusterization, self.conversation
            ),
            "current_page": "stereotypes",
            "groups": groups,
            "form": form,
        }


@method_decorator([login_required, can_edit_conversation], name="dispatch")
class StereotypeVotesCreateView(CreateView):
    def get(
        self, request: HttpRequest, conversation_id, *args: str, **kwargs: Any
    ) -> HttpResponse:
        conversation = Conversation.objects.get(id=conversation_id)
        kwargs = conversation.get_url_kwargs()
        return redirect(reverse("boards:stereotype-votes-list", kwargs=kwargs))

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        comment = request.POST.get("comment")
        stereotype_id = request.POST.get("author")
        choice = request.POST.get("choice")
        stereotype_vote = StereotypeVote.objects.create(
            choice=int(choice), comment_id=comment, author_id=stereotype_id
        )
        return HttpResponse(stereotype_vote.id)


@method_decorator([login_required, can_edit_conversation], name="dispatch")
class StereotypeVotesDeleteView(DeleteView):
    model = StereotypeVote
    success_url = "/"

    def get_object(self, queryset=None):
        id = self.kwargs["pk"]
        return self.get_queryset().filter(pk=id).get()


@method_decorator([login_required, can_edit_conversation], name="dispatch")
class StereotypeVotesUpdateView(UpdateView):
    model = StereotypeVote
    fields = ["choice"]

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        data = request.POST
        id = self.kwargs["pk"]

        vote = StereotypeVote.objects.get(pk=id)
        vote.choice = Stereotype.get_choice_value(data["choice"])
        vote.save()
        return HttpResponse(id)
