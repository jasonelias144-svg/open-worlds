def test_long_run_produces_journal():
    journal = run_between_sessions_long_run(seed=42, n_sessions=20)
    # A journal with multiple sessions
    assert len(journal) > 5
    # Final book exists
    assert journal.final_book() is not None
    # Trajectory has multiple points
    assert len(journal.trajectory()) == len(journal)


def test_long_run_has_rest_sessions():
    journal = run_between_sessions_long_run(seed=42, n_sessions=20)
    rest = journal.rest_sessions()
    # Some sessions must have written nothing
    assert len(rest) >= 1
    # Rest sessions still have postures
    for s in rest:
        assert s.posture in (SessionPosture.PATIENT,
                             SessionPosture.STRUGGLING,
                             SessionPosture.SETTLED)


def test_long_run_settles():
    journal = run_between_sessions_long_run(seed=42, n_sessions=40)
    # Final session is a settle
    assert journal.sessions[-1].phase == SessionPhase.SETTLE
    # The book has converged
    assert journal.final_book().converged


def test_long_run_journal_is_date_stamped():
    journal = run_between_sessions_long_run(seed=42, n_sessions=10)
    # Dates are spaced 3 days apart
    for i in range(1, len(journal)):
        delta = (journal.sessions[i].date
                 - journal.sessions[i-1].date).days
        assert delta == 3
