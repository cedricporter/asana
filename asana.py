#!/usr/bin/env python

import requests
import optparse
import getpass
import time
try:
    import simplejson as json
except ImportError:
    import json
from pprint import pprint

class AsanaAPI(object):

    def __init__(self, apikey, debug=False):
        self.debug = debug
        self.asana_url = "https://app.asana.com/api"
        self.api_version = "1.0"
        self.aurl = "/".join([self.asana_url, self.api_version])
        self.apikey = apikey
        self.bauth = self.get_basic_auth()

    def get_basic_auth(self):
        """Get basic auth creds
        :returns: the basic auth string
        """
        s = self.apikey + ":"
        return s.encode("base64").rstrip()

    def _asana(self, api_target):
        target = "/".join([self.aurl, api_target])
        if self.debug:
            print "-> Calling: %s" % target
        r = requests.get(target, auth=(self.apikey, ""))
        if self._ok_status(r.status_code) and r.status_code is not 404:
            if r.headers['content-type'] == 'application/json':
                return json.loads(r.text)['data']
            else:
                raise Exception('Did not receive json from api')
        else:
            if self.debug:
                print "-> Got: %s" % r.status_code
                print "-> %s" % r.text
            raise Exception('Received non 2xx or 404 status code on call')

    def _asana_post(self, api_target, data):
        target = "/".join([self.aurl, api_target])
        if self.debug:
            print "-> Posting to: %s" % target
            print "-> Post payload:"
            pprint(data)
        r = requests.post(target, auth=(self.apikey, ""), data=data)
        if self._ok_status(r.status_code) and r.status_code is not 404:
            if r.headers['content-type'] == 'application/json':
                return json.loads(r.text)['data']
            else:
                raise Exception('Did not receive json from api')
        else:
            if self.debug:
                print "-> Got: %s" % r.status_code
                print "-> %s" % r.text
            raise Exception('Received non 2xx or 404 status code on call')

    def _ok_status(self, status_code):
        if status_code/200 is 1:
            return True
        elif status_code/400 is 1:
            if status_code is 404:
                return True
            else:
                return False
        elif status_code is 500:
            return False

    def user_info(self, user_id="me"):
        return self._asana('users/%s' % user_id)

    def list_users(self, workspace=None, filters=[]):
        if workspace:
            return "Not yet available"
        else:
            if filters:
                fkeys = [x.strip().lower() for x in filters]
                fields = ",".join(fkeys)
                return self._asana('users?opt_fields=%s' % fields)
            else:
                return self._asana('users')

    def list_tasks(self, workspace, assignee):
        target = "tasks?workspace=%s&assignee=%s" % (workspace, assignee)
        return self._asana(target)

    def get_task(self, task_id):
        return self._asana("tasks/%s" % task_id)

    def list_projects(self, workspace=None):
        if workspace:
            return self._asana('workspaces/%s/projects' % workspace)
        else:
            return self._asana('projects')

    def get_project(self, project_id):
        return self._asana('projects/%s' % project_id)

    def get_project_tasks(self, project_id):
        return self._asana('projects/%s/tasks' % project_id)

    def list_stories(self, task_id):
        return self._asana('tasks/%s/stories' % task_id)

    def get_story(self, story_id):
        return self._asana('stories/%s' % story_id)

    def list_workspaces(self):
        return self._asana('workspaces')

    def create_task(self, name, workspace, assignee=None, assignee_status=None,
                    completed=False, due_on=None, followers=None, notes=None):
        #payload base
        payload = {'assignee': assignee or 'me', 'name': name, 
                   'workspace': workspace}
        if assignee_status in ['inbox', 'later', 'today', 'upcoming']:
            payload['assignee_status'] = assignee_status
        if completed:
            payload['completed'] = 'true'
        if due_on:
            try:
                vd = time.strptime(due_on, '%Y-%m-%d')
            except ValueError:
                raise Exception('Bad task due date: %s' % due_on)
        if followers:
            for pos, person in enumerate(followers):
                payload['follower[%d]' % pos] = person
        if notes:
            payload['notes'] = notes
        return self._asana_post('tasks', payload)

