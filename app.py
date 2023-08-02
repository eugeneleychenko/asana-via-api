import streamlit as st
import asana
from fuzzywuzzy import fuzz
from dotenv import find_dotenv, load_dotenv
import os

load_dotenv(find_dotenv())


# ASANA_URL = "https://app.asana.com/api/1.0"
# HEADERS = {
#     "Authorization": "Bearer " + os.getenv("asana_key")
# }

# Create a client
client = asana.Client.access_token(os.getenv("asana_key"))

# Get all workspaces
def get_workspaces():
    workspaces = []
    result = client.workspaces.get_workspaces()
    for workspace in result:
        workspaces.append(workspace['name'])
    return workspaces

# Get all projects in a workspace
def get_projects(workspace_id):
    projects = []
    result = client.projects.get_projects(workspace=workspace_id)
    for project in result:
        projects.append((project['name'], project['gid']))  # Store both name and ID
    return projects

# Get all sections in a project
def get_sections(project_id):
    sections = []
    result = client.sections.get_sections_for_project(project_id)
    for section in result:
        sections.append(section['name'])
    return sections

# Get all tasks in a section
def get_tasks(section_id):
    tasks = []
    result = client.tasks.get_tasks_for_section(section_id)
    for task in result:
        tasks.append(task['name'])
    return tasks

# Perform fuzzy search on projects
def fuzzy_search_project(workspace_id, search_query, threshold):
    projects = get_projects(workspace_id)
    search_results = []
    for project in projects:
        similarity = fuzz.token_set_ratio(search_query, project)
        if similarity >= threshold:
            search_results.append(project)
    return search_results

# Perform fuzzy search on sections
def fuzzy_search_section(project_id, search_query, threshold):
    sections = get_sections(project_id)
    search_results = []
    for section in sections:
        similarity = fuzz.token_set_ratio(search_query, section)
        if similarity >= threshold:
            search_results.append(section)
    return search_results

# Perform fuzzy search on tasks
def fuzzy_search_task(section_id, search_query, threshold):
    tasks = get_tasks(section_id)
    search_results = []
    for task in tasks:
        similarity = fuzz.token_set_ratio(search_query, task)
        if similarity >= threshold:
            search_results.append(task)
    return search_results

# Create a comment on a task
def create_comment(project_id, task_name, comment_text):
    task_id = None
    result = client.tasks.get_tasks_for_project(project_id)
    for task in result:
        if task['name'] == task_name:
            task_id = task['id']
            break
    if task_id:
        client.tasks.add_comment(task_id, {'text': comment_text})
        st.success('Comment added successfully.')
    else:
        st.error('Task not found.')

# Move a task to another section
def move_task(project_id, task_name, section_name):
    task_id = None
    section_id = None
    result = client.tasks.get_tasks_for_project(project_id)
    for task in result:
        if task['name'] == task_name:
            task_id = task['id']
            break
    if task_id:
        sections = client.sections.get_sections_for_project(project_id)
        for section in sections:
            if section['name'] == section_name:
                section_id = section['id']
                break
        if section_id:
            client.tasks.update_task(task_id, {'section': section_id})
            st.success('Task moved successfully.')
        else:
            st.error('Section not found.')
    else:
        st.error('Task not found.')

# Add a user to a task
def add_user_to_task(project_id, task_name, username):
    task_id = None
    result = client.tasks.get_tasks_for_project(project_id)
    for task in result:
        if task['name'] == task_name:
            task_id = task['id']
            break
    if task_id:
        user_id = None
        users = client.users.get_users()
        for user in users:
            if user['name'] == username:
                user_id = user['id']
                break
        if user_id:
            client.tasks.add_follower(task_id, {'user': user_id})
            st.success('User added to task successfully.')
        else:
            st.error('User not found.')
    else:
        st.error('Task not found.')

# Create a task and place it in a section
def create_task(project_id, task_name, section_name):
    section_id = None
    sections = client.sections.get_sections_for_project(project_id)
    for section in sections:
        if section['name'] == section_name:
            section_id = section['id']
            break
    if section_id:
        client.tasks.create_task({'projects': [project_id], 'name': task_name, 'section': section_id})
        st.success('Task created successfully.')
    else:
        st.error('Section not found.')

# Streamlit app
st.title('Asana Task Manager')

# Workspace selection
workspace = st.selectbox('Workspace', get_workspaces())
workspace_id = None
workspaces = client.workspaces.get_workspaces()
for ws in workspaces:
    if ws['name'] == workspace:
        workspace_id = ws['gid']
        break

# Task creation form
st.header('Create a Task')
new_task_name = st.text_input('Task Name')
new_task_section = st.text_input('Section Name')

# Get projects in the selected workspace
projects = get_projects(workspace_id)
project_names = [project[0] for project in projects]
project_dropdown = st.selectbox('Project', project_names)

if st.button('Create Task'):
    if workspace_id:
        selected_project = projects[project_names.index(project_dropdown)]
        project_id = selected_project[1]
        create_task(project_id, new_task_name, new_task_section)
    else:
        st.error('Workspace not found.')

# Comment creation form
st.header('Create a Comment')
comment_project = st.selectbox('Project', get_projects(workspace_id), key='comment_project')
comment_task = st.text_input('Task Name', key='comment_task')
comment_text = st.text_area('Comment Text')
if st.button('Add Comment'):
    create_comment(workspace_id, comment_task, comment_text)

# Task movement form
st.header('Move a Task')
move_project = st.selectbox('Project', get_projects(workspace_id), key='move_project')
move_task_name = st.text_input('Task Name', key='move_task_name')
move_section = st.text_input('Section Name', key='move_section')
if st.button('Move Task'):
    move_task(workspace_id, move_task_name, move_section)

# User addition form
st.header('Add User to Task')
user_project = st.selectbox('Project', get_projects(workspace_id), key='user_project')
user_task = st.text_input('Task Name', key='user_task')
user_name = st.text_input('Username', key='user_name')
if st.button('Add User'):
    add_user_to_task(workspace_id, user_task, user_name)

# Fuzzy search form
st.header('Fuzzy Search')
search_project = st.selectbox('Project', get_projects(workspace_id), key='search_project')
search_query = st.text_input('Search Query', key='search_query')
threshold = st.slider('Threshold', 0, 100, 80)

# Fuzzy search results
if st.button('Search'):
    st.subheader('Projects')
    project_results = fuzzy_search_project(workspace_id, search_query, threshold)
    for project in project_results:
        st.write(project)

    st.subheader('Sections')
    section_results = fuzzy_search_section('YOUR_PROJECT_ID', search_query, threshold)
    for section in section_results:
        st.write(section)

    st.subheader('Tasks')
    task_results = fuzzy_search_task('YOUR_SECTION_ID', search_query, threshold)
    for task in task_results:
        st.write(task)