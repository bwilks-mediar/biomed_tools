"""Core logic for fetching and processing ClinicalTrials.gov data."""

import json
from datetime import datetime
from typing import Dict, List

from loguru import logger
from sqlalchemy.orm import Session
from tqdm import tqdm

from . import config
from .api import ClinicalTrialsAPI
from .models import (
    AdverseEvent,
    Arm,
    ArmIntervention,
    ClinicalTrial,
    Condition,
    Eligibility,
    Intervention,
    Keyword,
    Location,
    Organization,
    Outcome,
    Reference,
    SearchTerm,
    SearchToTrial,
    TrialCondition,
    TrialKeyword,
    TrialOrganization,
    create_tables,
    get_session,
)
from .utils import normalize_query

# Configure logging when module is imported
config.configure_logging()


def fetch_all_trials(
    query: str, page_size: int = 100, save_path: str = None
) -> dict:
    """
    Fetch _all_ clinical trials matching `query` by following nextPageToken
    until exhausted. Optionally save the combined raw JSON.
    Returns a dict with:
      - "totalCount": int
      - "allStudies": list of study objects
    """
    all_studies = []
    next_token = None
    total_count = None
    
    api = ClinicalTrialsAPI()

    with tqdm(desc="Fetching trial pages", unit="page") as pbar:
        while True:
            params = {
                "query.term": query,
                "pageSize": page_size,
                "format": "json",
                "countTotal": "true",
            }
            if next_token:
                params["pageToken"] = next_token

            data = api.list_studies(params=params)
            
            if not data:
                break

            if total_count is None:
                total_count = data.get("totalCount", 0)
                pbar.total = (total_count + page_size - 1) // page_size

            page_studies = data.get("studies", [])
            all_studies.extend(page_studies)

            logger.info(
                f"Fetched {len(page_studies)} studies "
                f"(total so far: {len(all_studies)}/{total_count})"
            )
            pbar.update(1)

            next_token = data.get("nextPageToken")
            if not next_token:
                break

    result = {"totalCount": total_count, "studies": all_studies}

    if save_path:
        with open(save_path, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"🔖 All {len(all_studies)} studies saved to {save_path}")

    return result


def process_and_store_trial(session: Session, study: Dict, search_term_id: int):
    """
    Processes a single clinical trial study and stores its normalized data
    into the database.
    """
    proto = study.get("protocolSection", {})
    ident_mod = proto.get("identificationModule", {})
    status_mod = proto.get("statusModule", {})
    design_mod = proto.get("designModule", {})
    desc_mod = proto.get("descriptionModule", {})
    eligibility_mod = proto.get("eligibilityModule", {})

    nct_id = ident_mod.get("nctId")
    if not nct_id:
        logger.warning("Skipping study with no NCT ID.")
        return

    def _parse_date(date_struct):
        if date_struct and "date" in date_struct:
            try:
                return datetime.strptime(date_struct["date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                return None
        return None

    trial = ClinicalTrial(
        nct_id=nct_id,
        brief_title=ident_mod.get("briefTitle"),
        official_title=ident_mod.get("officialTitle"),
        acronym=ident_mod.get("acronym"),
        overall_status=status_mod.get("overallStatus"),
        start_date=_parse_date(status_mod.get("startDateStruct")),
        primary_completion_date=_parse_date(
            status_mod.get("primaryCompletionDateStruct")
        ),
        completion_date=_parse_date(status_mod.get("completionDateStruct")),
        study_first_submit_date=_parse_date(
            status_mod.get("studyFirstSubmitDateStruct")
        ),
        last_update_post_date=_parse_date(status_mod.get("lastUpdatePostDateStruct")),
        enrollment_count=design_mod.get("enrollmentInfo", {}).get("count"),
        study_type=design_mod.get("studyType"),
        brief_summary=desc_mod.get("briefSummary"),
        detailed_description=desc_mod.get("detailedDescription"),
        has_results=study.get("hasResults", False),
    )
    session.merge(trial)

    # Organizations
    orgs = [ident_mod.get("organization")] + proto.get(
        "sponsorCollaboratorsModule", {}
    ).get("collaborators", [])
    for org_data in orgs:
        if org_data and "fullName" in org_data:
            org = session.query(Organization).filter_by(name=org_data["fullName"]).first()
            if not org:
                org = Organization(
                    name=org_data["fullName"], class_=org_data.get("class")
                )
                session.add(org)
                session.flush()  # Get ID for the new org
            session.merge(
                TrialOrganization(
                    trial_nct_id=nct_id,
                    organization_id=org.id,
                    role="SPONSOR"
                    if org_data == ident_mod.get("organization")
                    else "COLLABORATOR",
                )
            )

    # Conditions
    for cond_name in proto.get("conditionsModule", {}).get("conditions", []):
        condition = session.query(Condition).filter_by(name=cond_name).first()
        if not condition:
            condition = Condition(name=cond_name)
            session.add(condition)
            session.flush()
        session.merge(
            TrialCondition(trial_nct_id=nct_id, condition_id=condition.id)
        )

    # Keywords
    for kw_name in proto.get("conditionsModule", {}).get("keywords", []):
        keyword = session.query(Keyword).filter_by(name=kw_name).first()
        if not keyword:
            keyword = Keyword(name=kw_name)
            session.add(keyword)
            session.flush()
        session.merge(TrialKeyword(trial_nct_id=nct_id, keyword_id=keyword.id))

    # Arms and Interventions
    arms_interventions = proto.get("armsInterventionsModule", {})
    for arm_data in arms_interventions.get("armGroups", []):
        arm = Arm(
            trial_nct_id=nct_id,
            label=arm_data.get("label"),
            type=arm_data.get("type"),
            description=arm_data.get("description"),
        )
        session.add(arm)
        session.flush()
        for int_name in arm_data.get("interventionNames", []):
            # Find the full intervention details
            int_details = next(
                (
                    i
                    for i in arms_interventions.get("interventions", [])
                    if i["name"] == int_name.split(": ")[-1]
                ),
                None,
            )
            if int_details:
                intervention = (
                    session.query(Intervention)
                    .filter_by(name=int_details["name"], type=int_details["type"])
                    .first()
                )
                if not intervention:
                    intervention = Intervention(
                        name=int_details["name"],
                        type=int_details["type"],
                        description=int_details.get("description"),
                    )
                    session.add(intervention)
                    session.flush()
                session.merge(
                    ArmIntervention(arm_id=arm.id, intervention_id=intervention.id)
                )

    # Outcomes
    for outcome_data in proto.get("outcomesModule", {}).get("primaryOutcomes", []) + proto.get(
        "outcomesModule", {}
    ).get("secondaryOutcomes", []):
        outcome = Outcome(
            trial_nct_id=nct_id,
            type=outcome_data.get("type"),
            measure=outcome_data.get("measure"),
            description=outcome_data.get("description"),
            time_frame=outcome_data.get("timeFrame"),
        )
        session.add(outcome)

    # Locations
    for loc_data in proto.get("contactsLocationsModule", {}).get("locations", []):
        location = Location(
            trial_nct_id=nct_id,
            facility=loc_data.get("facility"),
            city=loc_data.get("city"),
            state=loc_data.get("state"),
            zip=loc_data.get("zip"),
            country=loc_data.get("country"),
            latitude=loc_data.get("geoPoint", {}).get("lat"),
            longitude=loc_data.get("geoPoint", {}).get("lon"),
        )
        session.add(location)

    # References
    for ref_data in proto.get("referencesModule", {}).get("references", []):
        reference = Reference(
            trial_nct_id=nct_id,
            pmid=ref_data.get("pmid"),
            type=ref_data.get("type"),
            citation=ref_data.get("citation"),
        )
        session.add(reference)

    # Eligibility
    if eligibility_mod:
        eligibility = Eligibility(
            trial_nct_id=nct_id,
            criteria=eligibility_mod.get("eligibilityCriteria"),
            healthy_volunteers=eligibility_mod.get("healthyVolunteers"),
            sex=eligibility_mod.get("sex"),
            minimum_age=eligibility_mod.get("minimumAge"),
            maximum_age=eligibility_mod.get("maximumAge"),
        )
        session.add(eligibility)

    # Adverse Events
    results_section = study.get("resultsSection", {})
    if results_section:
        adverse_mod = results_section.get("adverseEventsModule", {})
        event_groups = {
            eg["id"]: eg["title"] for eg in adverse_mod.get("eventGroups", [])
        }
        for event_list, is_serious in [
            (adverse_mod.get("seriousEvents", []), True),
            (adverse_mod.get("otherEvents", []), False),
        ]:
            for event in event_list:
                for stat in event.get("stats", []):
                    adverse_event = AdverseEvent(
                        trial_nct_id=nct_id,
                        term=event.get("term"),
                        organ_system=event.get("organSystem"),
                        source_vocabulary=event.get("sourceVocabulary"),
                        assessment_type=event.get("assessmentType"),
                        is_serious=is_serious,
                        num_affected=stat.get("numAffected"),
                        num_at_risk=stat.get("numAtRisk"),
                        group_id=stat.get("groupId"),
                        group_title=event_groups.get(stat.get("groupId")),
                    )
                    session.add(adverse_event)

    session.merge(SearchToTrial(search_id=search_term_id, nct_id=nct_id))


def run_clinical_trials_query(query: str, max_records: int = 9999) -> int:
    """
    Main function to run a ClinicalTrials.gov query, fetch data, and store it.
    Returns the number of new trials downloaded.
    """
    create_tables()
    session = get_session()

    try:
        norm_query = normalize_query(query)
        search_term = session.query(SearchTerm).filter_by(term=norm_query).first()
        if not search_term:
            logger.info(f"Creating new search entry for query: '{query}'")
            search_term = SearchTerm(term=norm_query)
            session.add(search_term)
            session.commit()
        else:
            logger.info(f"✔️ Using existing search entry for query: '{query}'")

        logger.info(f"Searching ClinicalTrials.gov for query: '{query}'...")
        data = fetch_all_trials(query, page_size=config.CHUNK_SIZE)
        all_studies = data["studies"]
        count = data["totalCount"]

        if count == 0:
            logger.info("No trials found for this query.")
            return 0

        logger.info(f"Found {count} trials for this query.")

        if count > max_records:
            logger.warning(
                f"Query returned {count} results, but only fetching the first {max_records} as requested."
            )
            all_studies = all_studies[:max_records]

        nct_ids = [
            study["protocolSection"]["identificationModule"]["nctId"]
            for study in all_studies
            if "protocolSection" in study
            and "identificationModule" in study["protocolSection"]
        ]
        existing_nct_ids = {
            res[0]
            for res in session.query(ClinicalTrial.nct_id)
            .filter(ClinicalTrial.nct_id.in_(nct_ids))
            .all()
        }
        logger.info(
            f"Found {len(existing_nct_ids)} trials already in the database."
        )

        for nct_id in existing_nct_ids:
            session.merge(SearchToTrial(search_id=search_term.id, nct_id=nct_id))
        session.commit()

        new_studies = [
            study
            for study in all_studies
            if "protocolSection" in study
            and "identificationModule" in study["protocolSection"]
            and study["protocolSection"]["identificationModule"]["nctId"]
            not in existing_nct_ids
        ]
        logger.info(f"🔍 Processing and storing {len(new_studies)} new trials...")

        if not new_studies:
            logger.info("✅ All found trials were already in the database.")
            return 0

        for study in tqdm(new_studies, desc="Storing Trials"):
            process_and_store_trial(session, study, search_term.id)

        session.commit()
        logger.info("✅ Download and processing complete.")
        return len(new_studies)

    except Exception as e:
        logger.exception(f"An unexpected error occurred during the process: {e}")
        session.rollback()
        return 0
    finally:
        session.close()
        logger.info("Database session closed.")
