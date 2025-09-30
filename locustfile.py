from locust import HttpUser, task, between
import random, string


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    token = None
    last_bookmark_id = None
    last_event_enrollment_id = None
    last_course_enrollment_id = None

    def on_start(self):
        self.login()

    def login(self):
        email = "student.doe@camphub.com"
        password = "student123"
        response = self.client.post(
            "/api/auth/signin", json={"email": email, "password": password}
        )
        if response.status_code == 200 and "access_token" in response.json():
            self.token = response.json()["access_token"]
        else:
            self.token = None

    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def random_user(self):
        rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return {
            "username": f"user_{rand}",
            "email": f"user_{rand}@camphub.com",
            "password": "test1234",
            "first_name": "Locust",
            "last_name": "Test",
            "birth_date": "2000-01-01",
            "faculty_id": 1,
            "year_of_study": 1,
            "role_id": 2,
        }

    @task(0)
    def signup(self):
        self.client.post("/api/auth/signup", json=self.random_user())

    @task
    def get_me(self):
        self.client.get("/api/user", headers=self.auth_headers())

    @task
    def update_me(self):
        update_data = {"first_name": "Locust", "last_name": "Updated"}
        self.client.put("/api/user", json=update_data, headers=self.auth_headers())

    @task
    def get_faculties(self):
        self.client.get("/api/faculty", headers=self.auth_headers())

    @task
    def get_announcements(self):
        self.client.get("/api/annc")

    @task
    def get_announcement_categories(self):
        self.client.get("/api/annc/categories")

    @task
    def get_announcements_by_category(self):
        self.client.get("/api/annc/by-category/ทั่วไป")

    @task
    def get_announcement_by_id(self):
        self.client.get("/api/annc/1")

    @task
    def add_bookmark(self):
        if not self.last_bookmark_id:
            annc_id = 1
            with self.client.post(
                f"/api/annc/bookmarks/{annc_id}",
                headers=self.auth_headers(),
                catch_response=True,
            ) as res:
                if res.status_code == 200:
                    self.last_bookmark_id = res.json().get("id")
                    res.success()
                elif res.status_code == 400:
                    detail = res.json().get("detail", "")
                    if "bookmark ข่าวประกาศนี้แล้ว" in detail:
                        res.success()
                    else:
                        res.failure(res.text)
                else:
                    res.failure(res.text)

    @task
    def get_bookmarks(self):
        with self.client.get(
            "/api/annc/bookmarks?page=1&per_page=10",
            headers=self.auth_headers(),
            catch_response=True,
        ) as res:
            if res.status_code == 200:
                res.success()
            elif res.status_code == 422:
                res.success()
            else:
                res.failure(res.text)

    @task
    def remove_bookmark(self):
        if self.last_bookmark_id:
            with self.client.delete(
                f"/api/annc/bookmarks/{self.last_bookmark_id}",
                headers=self.auth_headers(),
                catch_response=True,
            ) as res:
                if res.status_code == 200:
                    self.last_bookmark_id = None
                    res.success()
                elif res.status_code == 404:
                    res.success()
                else:
                    res.failure(res.text)

    @task
    def get_events(self):
        self.client.get("/api/events", headers=self.auth_headers())

    @task
    def get_event_by_id(self):
        self.client.get("/api/events/1", headers=self.auth_headers())

    @task
    def enroll_event(self):
        if not self.last_event_enrollment_id:
            with self.client.post(
                "/api/event-enrollments/enroll",
                json={"event_id": 1},
                headers=self.auth_headers(),
                catch_response=True,
            ) as res:
                if res.status_code == 200:
                    self.last_event_enrollment_id = res.json().get("id")
                    res.success()
                elif res.status_code == 400:
                    detail = res.json().get("detail", "")
                    if "สมัครกิจกรรมนี้แล้ว" in detail:
                        res.success()
                    else:
                        res.failure(res.text)
                else:
                    res.failure(res.text)

    @task
    def get_event_enrollments(self):
        self.client.get("/api/event-enrollments/user", headers=self.auth_headers())

    @task
    def cancel_event_enrollment(self):
        if self.last_event_enrollment_id:
            with self.client.delete(
                f"/api/event-enrollments/cancel/{self.last_event_enrollment_id}",
                headers=self.auth_headers(),
                catch_response=True,
            ) as res:
                if res.status_code == 200:
                    self.last_event_enrollment_id = None
                    res.success()
                elif res.status_code == 404:
                    res.success()
                else:
                    res.failure(res.text)

    @task
    def get_courses(self):
        self.client.get("/api/courses", headers=self.auth_headers())

    @task
    def get_course_by_id(self):
        self.client.get("/api/courses/1", headers=self.auth_headers())

    @task
    def enroll_course(self):
        if not self.last_course_enrollment_id:
            with self.client.post(
                "/api/enrollments/enroll",
                json={"course_id": 1},
                headers=self.auth_headers(),
                catch_response=True,
            ) as res:
                if res.status_code == 200:
                    self.last_course_enrollment_id = res.json().get("id")
                    res.success()
                elif res.status_code == 400:
                    detail = res.json().get("detail", "")
                    if "สมัครรายวิชานี้แล้ว" in detail or "enrolled" in detail:
                        res.success()
                    else:
                        res.failure(res.text)
                else:
                    res.failure(res.text)

    @task
    def get_enrolled_courses(self):
        self.client.get("/api/enrollments/me", headers=self.auth_headers())

    @task
    def cancel_course_enrollment(self):
        if self.last_course_enrollment_id:
            with self.client.delete(
                f"/api/enrollments/cancel/{self.last_course_enrollment_id}",
                headers=self.auth_headers(),
                catch_response=True,
            ) as res:
                if res.status_code == 200:
                    self.last_course_enrollment_id = None
                    res.success()
                elif res.status_code == 404:
                    res.success()
                else:
                    res.failure(res.text)

    @task
    def get_course_schedule(self):
        self.client.get("/api/course_schedules", headers=self.auth_headers())

    @task
    def get_rooms(self):
        self.client.get("/api/room", headers=self.auth_headers())

    @task
    def get_locations(self):
        self.client.get("/api/location", headers=self.auth_headers())

    @task
    def get_location_by_id(self):
        self.client.get("/api/location/1", headers=self.auth_headers())
