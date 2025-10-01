from locust import HttpUser, task, between
import random, string


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    token = None
    user_email = None
    user_password = None

    last_bookmark_id = None
    last_event_enrollment_id = None
    last_course_enrollment_id = None

    # --------------------------
    # Lifecycle
    # --------------------------
    def on_start(self):
        # สมัคร user + login ก่อนเริ่ม task
        self.do_signup_and_login()

    # --------------------------
    # Utils
    # --------------------------
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

    # --------------------------
    # Signup + Login (utility)
    # --------------------------
    def do_signup_and_login(self):
        user_data = self.random_user()
        res = self.client.post("/api/auth/signup", json=user_data)
        if res.status_code in (200, 201):
            body = res.json()
            if "access_token" in body:
                self.token = body["access_token"]
                self.user_email = user_data["email"]
                self.user_password = user_data["password"]
            else:
                self.token = None
        else:
            self.token = None

    # --------------------------
    # Tasks
    # --------------------------

    @task(1)
    def signup_task(self):
        """จำลอง load signup อย่างเดียว"""
        user_data = self.random_user()
        self.client.post("/api/auth/signup", json=user_data)

    @task
    def get_me(self):
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/user", headers=self.auth_headers())

    @task
    def update_me(self):
        if not self.token:
            self.do_signup_and_login()
        update_data = {"first_name": "Locust", "last_name": "Updated"}
        self.client.put("/api/user", json=update_data, headers=self.auth_headers())

    @task
    def get_faculties(self):
        if not self.token:
            self.do_signup_and_login()
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
        if not self.token:
            self.do_signup_and_login()
        annc_id = 1
        with self.client.post(
            f"/api/annc/bookmarks/{annc_id}",
            headers=self.auth_headers(),
            catch_response=True,
        ) as res:
            if res.status_code == 200:
                res.success()
            elif res.status_code == 400:
                detail = res.json().get("detail", "")
                if "bookmark" in detail or "bookmark ข่าวประกาศนี้แล้ว" in detail:
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
            if res.status_code in (200, 422):
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
                if res.status_code in (200, 404):
                    self.last_bookmark_id = None
                    res.success()
                else:
                    res.failure(res.text)

    @task
    def get_events(self):
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/events", headers=self.auth_headers())

    @task
    def get_event_by_id(self):
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/events/1", headers=self.auth_headers())

    @task
    def enroll_event(self):
        if not self.token:
            self.do_signup_and_login()
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
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/event-enrollments/user", headers=self.auth_headers())

    @task
    def cancel_event_enrollment(self):
        if self.last_event_enrollment_id:
            with self.client.delete(
                f"/api/event-enrollments/cancel/{self.last_event_enrollment_id}",
                headers=self.auth_headers(),
                catch_response=True,
            ) as res:
                if res.status_code in (200, 404):
                    self.last_event_enrollment_id = None
                    res.success()
                else:
                    res.failure(res.text)

    @task
    def get_courses(self):
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/courses", headers=self.auth_headers())

    @task
    def get_course_by_id(self):
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/courses/1", headers=self.auth_headers())

    @task
    def enroll_course(self):
        if not self.token:
            self.do_signup_and_login()
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
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/enrollments/me", headers=self.auth_headers())

    @task
    def cancel_course_enrollment(self):
        if self.last_course_enrollment_id:
            with self.client.delete(
                f"/api/enrollments/cancel/{self.last_course_enrollment_id}",
                headers=self.auth_headers(),
                catch_response=True,
            ) as res:
                if res.status_code in (200, 404):
                    self.last_course_enrollment_id = None
                    res.success()
                else:
                    res.failure(res.text)

    @task
    def get_course_schedule(self):
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/course_schedules", headers=self.auth_headers())

    @task
    def get_rooms(self):
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/room", headers=self.auth_headers())

    @task
    def get_locations(self):
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/location", headers=self.auth_headers())

    @task
    def get_location_by_id(self):
        if not self.token:
            self.do_signup_and_login()
        self.client.get("/api/location/1", headers=self.auth_headers())
