#COS 730 - Assignment 2
#Task 1: Baseline Implementation (Correctness Phase)
#Implementation of the Intelligent Submission and Review System as per the provided sequence diagram.
import random

# VALIDATION
#SubmissionController >> Validator: validateFormat(data)
# Validator >> SubmissionController: valid / invalid
class Validator:

    def validate_format(self, data):

        #These are the fields defined as required for every submission.
        required_fields = ["title", "author", "abstract", "content"]

        #Check if required field exists and is not just empty spaces(Invalid if missing or empty)
        for field in required_fields:
            if field not in data or data[field].strip() == "":
                print(f"  [Validator] INVALID - missing field: '{field}'")
                return False

        print("  [Validator] VALID - all required fields are present")
        return True


# DATABASE
# saveSubmission(data) >> confirmation
# fetchReviewers()     >> reviewerList
# saveScore(score)

class Database:

    def __init__(self):
        self.submissions = {}   # stores saved submissions
        self.scores      = {}   # stores scores per submission
        self.id_counter  = 1    # auto-increments submission IDs

        # Hardcoded reviewers to simulate what would come from a real DB
        self.reviewers = [
            {"id": "R1", "name": "Alice",   "workload": 1, "conflicts": []},
            {"id": "R2", "name": "Bob",     "workload": 3, "conflicts": ["SUB-002"]},
            {"id": "R3", "name": "Charlie", "workload": 0, "conflicts": []},
            {"id": "R4", "name": "Diana",   "workload": 2, "conflicts": []},
            {"id": "R5", "name": "Eve",     "workload": 5, "conflicts": []},  # overloaded
        ]

    def save_submission(self, data):
        #Saves the submission and returns a confirmation ID.
        sub_id = f"SUB-{self.id_counter:03d}"
        self.id_counter += 1
        self.submissions[sub_id] = data
        self.scores[sub_id] = []
        print(f"  [Database] Submission saved. Confirmation ID = {sub_id}")
        return sub_id

    def fetch_reviewers(self):
        #Returns the full list of all reviewers.
        print(f"  [Database] Fetching reviewers... {len(self.reviewers)} found")
        return self.reviewers

    def save_score(self, sub_id, reviewer_name, score):
        #Save reviewer's score to the submission's score list
        self.scores[sub_id].append(score)
        print(f"  [Database] Score saved: {reviewer_name} gave {score} for {sub_id}")


# REVIEWER MANAGER
#getAvailableReviewers()
# fetchReviewers()           >> reviewerList
# filterConflicts()          (self-call)
# checkWorkload()            (self-call)
#  >> filteredReviewers

class ReviewerManager:

    def __init__(self, database):
        # Tight coupling-a baseline design flaw
        self.database = database  

    def get_available_reviewers(self, sub_id):
    #Fetches all reviewers then applies two separate filters.

        # Step 1: get the full list from the database
        reviewer_list = self.database.fetch_reviewers()

        # Step 2: filter out reviewers with conflicts (self-call in diagram)
        reviewer_list = self.filter_conflicts(reviewer_list, sub_id)

        # Step 3: filter out overloaded reviewers (self-call in diagram)
        reviewer_list = self.check_workload(reviewer_list)

        print(f"  [ReviewerManager] Final filtered list: {[r['name'] for r in reviewer_list]}")
        return reviewer_list


    def filter_conflicts(self, reviewer_list, sub_id):
        #Removes reviewers who have a conflict with this submission.
        filtered = [r for r in reviewer_list if sub_id not in r["conflicts"]]
        print(f"  [ReviewerManager] After conflict filter: {[r['name'] for r in filtered]}")
        return filtered

    def check_workload(self, reviewer_list):
        # Removes reviewers who are overloaded (workload >= 4).
        filtered = [r for r in reviewer_list if r["workload"] < 4]
        print(f"  [ReviewerManager] After workload filter: {[r['name'] for r in filtered]}")
        return filtered

    #Reviewer
    #Assign_reviewer
    #Generate and submit it to EvaluationManager via submitScore(score)
    class Reviewer:

     def __init__(self, reviewer_info):
        # Store the reviewer's details from the database record
        self.info = reviewer_info
        self.assigned_sub_id = None

    def assign_review(self, sub_id):
        # Called by SubmissionController in the assign reviewers loop
        # loop [assign reviewers] >> assignReview()
        self.assigned_sub_id = sub_id
        print("[Reviewer] " + self.info["name"] + " assigned to review " + sub_id)

    def submit_score(self, evaluation_manager):
        # Generate a random score between 1 and 10 to simulate a real review
        #loop [each reviewer] >> submitScore(score)
        score = round(random.uniform(1.0, 10.0), 2)
        print("[Reviewer] " + self.info["name"] + " submitting score: " + str(score))

        # Pass the score to EvaluationManager
        # Reviewer holding a reference to EvaluationManager is a design flaw
        evaluation_manager.submit_score(self.assigned_sub_id, self.info["name"], score)


# EVALUATION MANAGER
# startEvaluation()
# submitScore(score)    << called per reviewer
# saveScore(score)      >> Database
# calculateAverage()    (self-call)
# checkConsensus()      (self-call)
# applyRules()          (self-call)
#
# BASELINE FLAW: Coupled to both Database and NotificationService
# BASELINE FLAW: Decision logic (thresholds) hardcoded here

class EvaluationManager:

    ACCEPT_THRESHOLD   = 7.0   # average must be >= this to accept
    REJECT_THRESHOLD   = 4.0   # average below this means rejected
    CONSENSUS_VARIANCE = 2.5   # max allowed variance for consensus

    def __init__(self, database, notification_service):
        self.database             = database              # tight coupling (flaw)
        self.notification_service = notification_service  # tight coupling (flaw)
        self.scores = {}

    def start_evaluation(self, sub_id):
        #Initialises score tracking for this submission.
        self.scores[sub_id] = []
        print("[EvaluationManager] Started evaluation for " + sub_id)

    def submit_score(self, sub_id, reviewer_name, score):
       
        #Receives a score from a reviewer and Save score to database and store it locally for calculations.
        self.database.save_score(sub_id, reviewer_name, score)  # saveScore(score)
        self.scores[sub_id].append(score)

    def calculate_average(self, sub_id):
        #Calculates the average of all reviewer scores.
        scores = self.scores[sub_id]
        avg = sum(scores) / len(scores)
        print(f"  [EvaluationManager] Average score = {avg:.2f}")
        return avg

    def check_consensus(self, sub_id):
        #Checks if reviewers broadly agree by measuring score variance.
        # Variance tells us how much reviewers disagree
        # Low variance = they mostly agree, high variance = big disagreement
        scores = self.scores[sub_id]
        avg = sum(scores) / len(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        consensus = variance <= self.CONSENSUS_VARIANCE
        print(f"  [EvaluationManager] Variance = {variance:.2f}, Consensus = {consensus}")
        return consensus

    def apply_rules(self, sub_id):
        #Decides the outcome based on average score and consensus.
        #Baseline flaw: scattered if/elif logic with magic numbers.
        avg       = self.calculate_average(sub_id)
        consensus = self.check_consensus(sub_id)

        if avg >= self.ACCEPT_THRESHOLD and consensus:
            outcome = "accepted"
        elif avg < self.REJECT_THRESHOLD:
            outcome = "rejected"
        else:
            outcome = "revision"

        print(f"  [EvaluationManager] Outcome = {outcome}")
        return outcome

    def finalise(self, sub_id):
        #Runs applyRules then triggers the correct notification method.
        # alt [accepted / rejected / revision]
       
        outcome = self.apply_rules(sub_id)

        if outcome == "accepted":
            self.notification_service.notify_acceptance(sub_id)
        elif outcome == "rejected":
            self.notification_service.notify_rejection(sub_id)
        else:
            self.notification_service.notify_revision(sub_id)

        return outcome


# NOTIFICATION SERVICE
# alt [accepted]  >> notifyAcceptance()
# alt [rejected]  >> notifyRejection()
# alt [revision]  >> notifyRevision()
# sendNotification() >> Researcher
# =============================================================
class NotificationService:

    def notify_acceptance(self, sub_id):
        # alt [accepted]  >> notifyAcceptance()
        self._send(sub_id, "ACCEPTED",
                   "Congratulations! Your submission has been accepted.")

    def notify_rejection(self, sub_id):
        # alt [rejected]  >> notifyRejection()
        self._send(sub_id, "REJECTED",
                   "Sorry, your submission has been rejected.")

    def notify_revision(self, sub_id):
        # alt [revision]  >> notifyRevision()
        self._send(sub_id, "REVISION REQUIRED",
                   "Your submission needs revisions before it can be accepted.")

    def _send(self, sub_id, status, message):
        #Simulates sending a notification email to the Researcher.
        print(f"  [NotificationService] --> Researcher notified:")
        print(f"      Submission : {sub_id}")
        print(f"      Status     : {status}")
        print(f"      Message    : {message}")


# SUBMISSION CONTROLLER
# UI -> SubmissionController: submit(data)
# BASELINE FLAW: Creates all objects itself = "God Class"
# BASELINE FLAW: Tightly coupled to every other component
class SubmissionController:

    NUM_REVIEWERS = 3  # The diagram doesn't specify this number so 3 was chosen as reasonable

    def __init__(self):
        # Creates all dependencies itself (God Class - baseline flaw)
        self.database             = Database()
        self.validator            = Validator()
        self.notification_service = NotificationService()
        self.reviewer_manager     = ReviewerManager(self.database)
        self.evaluation_manager   = EvaluationManager(
                                        self.database,
                                        self.notification_service
                                    )

    def submit(self, data):
        """
        Orchestrates the full submission pipeline.
        Follows the sequence diagram step by step.
        """
        print("\n  [SubmissionController] submit() called")

        # Step 1: validate the submission format
        #SubmissionController >> Validator: validateFormat(data)
        is_valid = self.validator.validate_format(data)

        if not is_valid:
            # alt [invalid]: return error to UI/Researcher
            return {"success": False, "error": "Invalid submission - missing required fields"}

        # Step 2: save the submission to the database
        # saveSubmission(data) >> confirmation
        sub_id = self.database.save_submission(data)

        ## Step 3: get available reviewers
        # getAvailableReviewers() >> filteredReviewers
        filtered_reviewers = self.reviewer_manager.get_available_reviewers(sub_id)

        if not filtered_reviewers:
            return {"success": False, "error": "No reviewers available"}

         # Step 4: start the evaluation process
         # startEvaluation()
        self.evaluation_manager.start_evaluation(sub_id)

        # Step 5: assign reviewers and collect scores
        # loop [assign reviewers] >> assignReview()
        # loop [each reviewer]   >> submitScore(score)
        assigned = filtered_reviewers[:self.NUM_REVIEWERS]
        print(f"  [SubmissionController] Assigning {len(assigned)} reviewers...")

        for reviewer in assigned:
            print(f"  [SubmissionController] assignReview() -> {reviewer['name']}")
            score = round(random.uniform(1.0, 10.0), 2)  # simulated reviewer score
            print(f"  [Reviewer:{reviewer['name']}] submitScore({score})")
            self.evaluation_manager.submit_score(sub_id, reviewer["name"], score)

        # Step 6: finalise evaluation - calculate average, check consensus, apply rules
        # calculateAverage(), checkConsensus(), applyRules()
        # Then triggers the correct notification branch
        outcome = self.evaluation_manager.finalise(sub_id)

        return {"success": True, "submission_id": sub_id, "outcome": outcome}


# UI
# Researcher -> UI: submitResearchOutput(data)
# UI -> SubmissionController: submit(data)
class UI:

    def __init__(self):
        self.controller = SubmissionController()

    def submit_research_output(self, data):
        """Receives input from Researcher and forwards to SubmissionController."""
        print("[UI] submitResearchOutput() -> forwarding to SubmissionController")
        result = self.controller.submit(data)

        if result["success"]:
            print(f"[UI] Complete. ID={result['submission_id']}, Outcome={result['outcome']}")
        else:
            print(f"[UI] Error returned to Researcher: {result['error']}")

        return result

# RESEARCHER (entry point)
# Researcher -> UI: submitResearchOutput(data)
if __name__ == "__main__":

    # Create the UI - entry point for the whole system
    ui = UI()

    # Test 1: Valid submission - should go through full pipeline
    print("\n" + "="*55)
    print("TEST 1: Valid Submission")
    print("="*55)
    ui.submit_research_output({
        "title":    "AI in Healthcare",
        "author":   "Dr. Jane Smith",
        "abstract": "This paper explores AI applications in diagnostics.",
        "content":  "Introduction: Artificial intelligence is transforming..."
    })

    # Test 2: Invalid submission - missing abstract
    # Should trigger alt [invalid] branch and return error
    print("\n" + "="*55)
    print("TEST 2: Invalid Submission (missing abstract)")
    print("="*55)
    ui.submit_research_output({
        "title":   "Incomplete Paper",
        "author":  "John Doe",
        "content": "Some content here..."
    })

    # Test 3: Another valid submission
    print("\n" + "="*55)
    print("TEST 3: Another Valid Submission")
    print("="*55)
    ui.submit_research_output({
        "title":    "Blockchain Security",
        "author":   "Prof. Alan Turing",
        "abstract": "We investigate blockchain vulnerabilities.",
        "content":  "Blockchain technology has grown significantly..."
    })
