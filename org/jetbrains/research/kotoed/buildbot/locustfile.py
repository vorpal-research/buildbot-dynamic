import string
from random import SystemRandom

from locust import TaskSet, task, HttpLocust


class UserBehavior(TaskSet):
    rnd = SystemRandom()

    def random_string(self):
        return ''.join(
            self.rnd.choice(string.ascii_uppercase + string.digits) for _ in range(self.rnd.randint(1, 20))
        )

    @task
    def do_it(self):
        random_project_name = self.random_string()
        random_project_url = self.random_string()
        self.client.post("/custom", {"project_name": f"{random_project_name}", "project_url": f"{random_project_url}"})


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
