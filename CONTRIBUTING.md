# Contributing to EV Charger Fault Detection AI

Thanks for helping. Bug reports, questions, documentation and code are welcome in **English or Thai** (ยินดีรับทั้งภาษาไทยและภาษาอังกฤษ).

## Ways to help

- **Use the app and report problems** with the [bug report](https://github.com/SukritJaAIproject/EV_Charger_Fault_Detection_AI/issues/new?template=bug_report.yml) or [feature request](https://github.com/SukritJaAIproject/EV_Charger_Fault_Detection_AI/issues/new?template=feature_request.yml) form. Include the edition and version from the dashboard header and your Windows version.
- **Start small:** [good first issues](https://github.com/SukritJaAIproject/EV_Charger_Fault_Detection_AI/labels/good%20first%20issue) are well scoped. [Help wanted](https://github.com/SukritJaAIproject/EV_Charger_Fault_Detection_AI/labels/help%20wanted) issues are bigger.
- **Ask questions or propose ideas** in [Discussions](https://github.com/SukritJaAIproject/EV_Charger_Fault_Detection_AI/discussions), for example about DIN 70121 / ISO 15118 behaviour you have seen on real chargers.

Comment on an issue before you start so two people don't work on the same thing.

## Never post identifying capture data

Don't attach captures or logs that identify a vehicle (EVCCID, MAC address), a station name or a location to a public issue. Describe the file instead, or ask for a private channel in the issue.

## Research code (`ev_charger_ai/`)

The pipeline, detectors, scoring and benchmark harness are plain Python. The fast regression tests need no fleet data. Run each file on its own from `ev_charger_ai/`:

```bash
cd ev_charger_ai
python tests/test_ground_truth_strict.py
python tests/test_ground_truth_iso_reviewed.py
python tests/test_slac_normative.py
python tests/test_slac_empirical_compat.py
```

These files set environment variables when they are imported, so running them together in one pytest process doesn't work yet ([#1](https://github.com/SukritJaAIproject/EV_Charger_Fault_Detection_AI/issues/1)).

The 41 GB session and feature data set is not in the repository, so the most useful contributions work without it:

- unit tests for pure functions such as scoring (`core/metrics.py`, [#2](https://github.com/SukritJaAIproject/EV_Charger_Fault_Detection_AI/issues/2)), labelling rules and feature trackers, using small synthetic inputs;
- documentation and English or Thai translations;
- making the scripts run on Linux and macOS as well as Windows ([#3](https://github.com/SukritJaAIproject/EV_Charger_Fault_Detection_AI/issues/3)).

*Reproducing the research* in the README lists the full pipeline and the environment variables that switch the experiment arms. Data roots are found by folder name (`core/findroot.py`) and can be overridden with `EV_AI_DATA`, `EV_AI_SESSIONS`, `EV_AI_ARTIFACTS` and `EV_AI_RESULTS`.

## Desktop app (`imps_platform/`)

The app is built inside an iMPS platform checkout with the patches in `imps_platform/patches/` applied. `imps_platform/desktop/README.md` is the full runbook.

## Pull requests

- One change per pull request, with a short note on what changed and how you tested it.
- Keep reported numbers reproducible: if a change moves a result, name the script and the result file that show it.
- Don't commit captures, session data, credentials or code-signing material.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
