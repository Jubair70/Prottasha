from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from rest_framework import filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import DjangoObjectPermissions

from onadata.libs.serializers.team_serializer import TeamSerializer
from onadata.apps.api.models import Team
from onadata.apps.api.tools import add_user_to_team, remove_user_from_team


class TeamViewSet(ModelViewSet):

    """
This endpoint allows you to create, update and view team information.

## GET List of Teams
Provides a json list of teams and the projects the team is assigned to.

<pre class="prettyprint">
<b>GET</b> /api/v1/teams
</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/teams

> Response
>
>        [
>            {
>                "url": "https://example.com/api/v1/teams/1",
>                "name": "Owners",
>                "organization": "bruize",
>                "projects": []
>            },
>            {
>                "url": "https://example.com/api/v1/teams/2",
>                "name": "demo team",
>                "organization": "bruize",
>                "projects": []
>            }
>        ]

## GET Team Info for a specific team.

Shows teams details and the projects the team is assigned to, where:

* `pk` - unique identifier for the team

<pre class="prettyprint">
<b>GET</b> /api/v1/teams/<code>{pk}</code>
</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/teams/1

> Response
>
>        {
>            "url": "https://example.com/api/v1/teams/1",
>            "name": "Owners",
>            "organization": "bruize",
>            "projects": []
>        }

## List members of a team

A list of usernames is the response for members of the team.

<pre class="prettyprint">
<b>GET</b> /api/v1/teams/<code>{pk}/members</code>
</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/teams/1/members

> Response
>
>       ["member1"]
>

## Add a user to a team

POST `{"username": "someusername"}`
to `/api/v1/teams/<pk>/members` to add a user to
the specified team.
A list of usernames is the response for members of the team.

<pre class="prettyprint">
<b>POST</b> /api/v1/teams/<code>{pk}</code>/members
</pre>

> Response
>
>       ["someusername"]

"""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    lookup_field = 'pk'
    extra_lookup_fields = None
    permission_classes = [DjangoObjectPermissions]
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    @action(methods=['DELETE', 'GET', 'POST'])
    def members(self, request, *args, **kwargs):
        team = self.get_object()
        data = {}
        status_code = status.HTTP_200_OK

        if request.method in ['DELETE', 'POST']:
            username = request.DATA.get('username') or\
                request.QUERY_PARAMS.get('username')

            if username:
                try:
                    user = User.objects.get(username__iexact=username)
                except User.DoesNotExist:
                    status_code = status.HTTP_400_BAD_REQUEST
                    data['username'] = [
                        _(u"User `%(username)s` does not exist."
                          % {'username': username})]
                else:
                    if request.method == 'POST':
                        add_user_to_team(team, user)
                    elif request.method == 'DELETE':
                        remove_user_from_team(team, user)
                    status_code = status.HTTP_201_CREATED
            else:
                status_code = status.HTTP_400_BAD_REQUEST
                data['username'] = [_(u"This field is required.")]

        if status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            data = [u.username for u in team.user_set.all()]

        return Response(data, status=status_code)
