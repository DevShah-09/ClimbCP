import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.database.base import Base
from app.models import CFUser, ContestParticipation, ProblemAttempt, Topic, AIReport, UserEmbedding
from app.services import codeforces_service as cf
from app.services import analytics_service as analytics
from app.services.ai_coach_service import _get_cached_report


def rating(contest=100, new=1200):
    return dict(contestId=contest, contestName=f'Round {contest}', rank=12,
                oldRating=1000, newRating=new, ratingUpdateTimeSeconds=1700000000)


def submission(index='A', verdict='OK', kind='CONTESTANT', contest=100, timestamp=1700000000):
    return dict(problem=dict(contestId=contest, index=index, name='Problem', rating=1000,
                             tags=['math']), verdict=verdict, author=dict(participantType=kind),
                creationTimeSeconds=timestamp, relativeTimeSeconds=300, programmingLanguage='GNU C++17')


class ProfileSyncTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine, autoflush=False)()
        self.db.add(Topic(name='Math'))
        self.db.commit()
        self.profile = dict(handle='TestUser', rating=1200, maxRating=1300)
        self.ratings = [rating()]
        self.submissions = [submission()]
        for name, value in [('get_user_info', self.profile), ('get_user_rating_history', self.ratings),
                            ('get_user_submissions', self.submissions)]:
            mock = patch.object(cf, name, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def sync(self):
        return cf.sync_user_data(self.db, 'testuser')

    def test_repeat_login_updates_latest_contest_rating_submissions_without_duplicates(self):
        first = self.sync()
        self.profile['rating'] = 1400
        self.ratings.append(rating(101, 1400))
        self.submissions.append(submission(contest=101))
        second = self.sync()
        summary = analytics.get_user_analytics(self.db, 'TESTUSER')
        self.assertEqual((summary.current_rating, summary.contest_count, summary.problems_solved), (1400, 2, 2))
        self.assertGreaterEqual(second['last_synced_at'], first['last_synced_at'])
        self.sync()
        self.assertEqual(self.db.query(CFUser).count(), 1)
        self.assertEqual(self.db.query(ProblemAttempt).count(), 2)
        self.assertEqual(self.db.query(ContestParticipation).count(), 2)

    def test_rejudge_and_practice_solve_refresh_without_inflating_contest_solves(self):
        self.submissions[:] = [submission(verdict='WRONG_ANSWER'), submission(kind='PRACTICE', timestamp=1700001000)]
        self.sync()
        self.assertEqual(self.db.query(ContestParticipation).one().problems_solved, 0)
        self.assertTrue(self.db.query(ProblemAttempt).one().solved)
        self.submissions[1]['verdict'] = 'WRONG_ANSWER'
        self.sync()
        self.assertFalse(self.db.query(ProblemAttempt).one().solved)

    def test_failed_sync_preserves_previous_snapshot(self):
        self.sync()
        previous = self.db.query(CFUser).one().last_synced_at
        self.profile['rating'] = 2000
        with patch.object(cf, 'get_user_submissions', side_effect=cf.CodeforcesTimeoutException('Timed out')):
            with self.assertRaises(cf.CodeforcesTimeoutException):
                self.sync()
        user = self.db.query(CFUser).one()
        self.assertEqual(user.current_rating, 1200)
        self.assertEqual(user.last_synced_at, previous)

    def test_database_reads_are_batched_and_rating_history_is_eager_loaded(self):
        self.submissions[:] = [submission(index=str(i)) for i in range(100)]
        self.ratings[:] = [rating(i) for i in range(100, 120)]
        self.sync()
        selects = []
        def collect(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith('SELECT'):
                selects.append(statement)
        event.listen(self.engine, 'before_cursor_execute', collect)
        self.sync()
        self.assertLessEqual(len(selects), 9, '\n'.join(selects))
        selects.clear()
        self.assertEqual(len(analytics.get_rating_history(self.db, 'TestUser')), 20)
        self.assertEqual(len(selects), 2)

    def test_ai_report_from_previous_sync_is_not_reused(self):
        self.sync()
        user = self.db.query(CFUser).one()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        report = AIReport(user_id=user.id, cache_key='test', summary='', strengths='',
                          weaknesses='', recommendations='', created_at=now-timedelta(minutes=1))
        self.db.add(report)
        self.db.commit()
        self.assertIsNone(_get_cached_report(self.db, 'test'))
        report.created_at = now + timedelta(seconds=1)
        self.db.commit()
        self.assertIsNotNone(_get_cached_report(self.db, 'test'))

    def test_similarity_vector_is_regenerated_after_sync(self):
        from app.services.user_embedding_service import find_similar_users
        self.sync()
        user = self.db.query(CFUser).one()
        vector = UserEmbedding(user_id=user.id, embedding=[0.0] * 128,
                               created_at=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(days=1))
        self.db.add(vector)
        self.db.commit()
        find_similar_users(self.db, 'TestUser')
        self.db.refresh(vector)
        self.assertGreaterEqual(vector.created_at, user.last_synced_at)
        self.assertTrue(any(vector.embedding))

    def test_empty_profile_is_supported(self):
        self.submissions.clear()
        self.ratings.clear()
        self.profile.pop('rating')
        self.sync()
        summary = analytics.get_user_analytics(self.db, 'TestUser')
        self.assertEqual(summary.total_submissions, 0)
        self.assertIsNone(summary.current_rating)


if __name__ == '__main__':
    unittest.main()
