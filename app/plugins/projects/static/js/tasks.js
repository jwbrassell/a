function viewTask(taskId) {
    // Implement view task logic
    console.log('View task:', taskId);
}

function editTask(taskId) {
    // Implement edit task logic
    console.log('Edit task:', taskId);
}

function deleteTask(taskId) {
    // Implement delete task logic with confirmation
    if (confirm('Are you sure you want to delete this task?')) {
        console.log('Delete task:', taskId);
    }
}

function saveNewTask() {
    // Implement save new task logic
    console.log('Save new task');
    $('#modal-new-task').modal('hide');
}
