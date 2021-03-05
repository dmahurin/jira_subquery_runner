# Use jira API to create subqueries
#
# Workaround for 10 year old jira bug - missing subqueries
# https://jira.atlassian.com/browse/JRASERVER-21936
#
# This set of functions allow queries from the result of other queries

import os
import subprocess
import json

token = None
email = None
url = None
epic_custom_field = None

def config (c):
	global url, email, token, epic_custom_field

	url = c['url']
	email = c['email']
	token = c['token']
	epic_custom_field = c['epic_custom_field']

def get_query_epics(query):
	issues = []
	startAt = 0;
	maxResults = 50;

	while(True):
		query=query.replace(' ', '%20').replace('"', '%22')
		proc = subprocess.Popen([ 'curl', '-s', '-u', email + ':' + token,
			'-X', 'GET', '-H', "Content-Type: application/json",
			url + '/rest/api/3/search?startAt=' + str(len(issues)) + '&fields=customfield_' + str(epic_custom_field) + '&jql=' +
			query ], 0, stdout = subprocess.PIPE)

		result = proc.communicate()[0].decode('utf-8')
		result = json.loads(result)
		issues.extend(result['issues'])
		if(len(issues) >= result['total']): break;
	issue_keys = {}
	for issue in issues:
		issue_keys[(issue['fields']['customfield_' + str(epic_custom_field) ])] = 1

	print("epics query resulted in " + str(len(issue_keys)) + " items")
	return issue_keys.keys()

def get_query_issues(query):
	issues = []
	startAt = 0;
	maxResults = 50;

	while(True):
		query=query.replace(' ', '%20').replace('"', '%22')
		proc = subprocess.Popen([ 'curl', '-s', '-u', email + ':' + token,
			'-X', 'GET', '-H', "Content-Type: application/json",
			url + '/rest/api/3/search?startAt=' + str(len(issues)) + '&fields=key&jql=' +
			query ], 0, stdout = subprocess.PIPE)

		result = proc.communicate()[0].decode('utf-8')
		result = json.loads(result)
		issues.extend(result['issues'])
		if(len(issues) >= result['total']): break;
	issue_keys = {}
	for issue in issues:
		issue_keys[issue['key']] = 1

	print("issue query resulted in " + str(len(issue_keys)) + " items")
	return issue_keys.keys()

def create_filter(name, query):
	number_suffix = ''
	method = 'POST'
	proc = subprocess.Popen([ 'curl', '-s', '-u', email + ':' + token,
		'-H', "Content-Type: application/json", '-H', 'Accept: application/json',
		'-X', 'GET',
		url + '/rest/api/3/filter/search?filterName=' + name
		], 0, stdout = subprocess.PIPE)
	result = proc.communicate()[0].decode('utf-8')
	result = json.loads(result)['values']
	number = result[0]['id'] if(len(result)) else None

	if(number != None):
		number_suffix = '/' + str(number)
		method = 'PUT'

	proc = subprocess.Popen([ 'curl', '-s',
		'-u', email + ':' + token,
		'-H', "Content-Type: application/json", '-H', 'Accept: application/json',
		'-X', method,
		'--data', '{"jql": "' + query.replace('"', '\\"') + '", "name": "' + name + '"}',
		url + '/rest/api/3/filter/' + number_suffix],
		0, stdout = subprocess.PIPE)
	result = proc.communicate()[0].decode('utf-8')

	print ('created ' + name if number == None else 'updated ' + name)

	result = json.loads(result)
	if ('id' not in result):
		print (result)
		return None

	return result['id']

