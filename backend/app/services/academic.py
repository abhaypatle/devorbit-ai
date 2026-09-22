from typing import Any


def generate_capstone_documents(specs: dict[str, Any]) -> dict[str, str]:
    title = specs["title"]
    problem = specs["problem_statement"]
    objectives = specs["objectives"]
    technologies = specs["technologies"]
    methodology = specs["methodology"]
    authors = specs.get("authors") or "DevOrbit AI Research Team"
    generation_mode = specs.get("generation_mode", "auto")
    custom_outline = specs.get("custom_outline", "")

    objective_lines = "\n".join(f"{index}. {objective}" for index, objective in enumerate(objectives, start=1))
    technology_lines = ", ".join(technologies)
    srs = f"""# Software Requirements Specification

## {title}

**Prepared by:** {authors}  
**Standard:** IEEE 830-style requirements specification  
**Status:** Draft for academic review

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for **{title}**. It provides a traceable baseline for implementation, evaluation, and viva defense.

### 1.2 Problem Statement
{problem}

### 1.3 Scope
The system will provide a measurable software solution using {technology_lines}. The scope includes the core user workflow, data processing, security controls, observability, and evaluation of the proposed approach.

## 2. Overall Description

### 2.1 Product Perspective
The solution is a modular application composed of a user interface, application services, persistence, and integration boundaries. Components should communicate through documented APIs and produce auditable outputs.

### 2.2 User Classes
- **Primary operator:** configures the system and reviews generated results.
- **End user:** uses the core workflow and consumes system outputs.
- **Evaluator:** validates requirements, experiments, results, and limitations.

## 3. Functional Requirements

{objective_lines}

### 3.1 Input Validation
The system shall validate required inputs, reject malformed requests, and provide actionable error messages without exposing secrets.

### 3.2 Auditability
The system shall record generation metadata, timestamps, and evaluation results so that important outputs can be reproduced.

## 4. Non-Functional Requirements

- **Performance:** normal API requests should complete within an agreed service-level target.
- **Security:** authentication, authorization, input validation, least privilege, and protected secrets shall be applied.
- **Reliability:** failures shall be isolated, observable, and recoverable without corrupting persisted data.
- **Maintainability:** modules shall have clear interfaces and automated tests.

## 5. System Design Constraints

- Implementation technologies: {technology_lines}.
- Development methodology: {methodology}.
- Deployment configuration shall separate development, testing, and production environments.

## 6. Verification and Acceptance

Each functional requirement shall map to a test case. Evaluation shall include unit tests, integration tests, security checks, usability observations, and comparison against the stated objectives.

## 7. Risks and Limitations

The draft requires validation with real users and representative data. Resource constraints, model limitations, integration failures, and changes in the deployment environment should be documented during experimentation.

## 8. References

- IEEE Recommended Practice for Software Requirements Specifications.
- Project-specific technical documentation and experiment records.
"""

    research = f"""# Research Paper Draft: {title}

## Abstract
This paper presents **{title}**, a software solution addressing the following problem: {problem} The proposed approach uses {technology_lines} and follows {methodology}. The system is evaluated against functional correctness, performance, security, and usability objectives.

## 1. Introduction
Software teams need reliable, explainable solutions for complex workflows. This research investigates how the proposed system can reduce operational friction while preserving traceability and measurable quality.

## 2. Problem Definition and Objectives
{problem}

The study objectives are:
{objective_lines}

## 3. Methodology
The project follows **{methodology}**. Requirements are converted into modular components, implemented iteratively, and evaluated using repeatable test cases and recorded observations.

## 4. Proposed System
The architecture separates presentation, application logic, data persistence, and external integrations. This separation supports independent testing, controlled failure handling, and future scalability.

## 5. Experimental Plan
Experiments will measure task completion, response time, error rate, resource usage, and user feedback. A baseline implementation should be compared with the proposed workflow using the same inputs and evaluation criteria.

## 6. Expected Results
The expected result is a working prototype with demonstrable improvements over the baseline. Results must include quantitative measurements, qualitative observations, threats to validity, and reproducibility details.

## 7. Conclusion and Future Work
The proposed system provides a foundation for the stated objectives. Future work may include broader datasets, additional integrations, stronger automation, and longitudinal evaluation.
"""

    slides = f"""# Viva Defense Presentation Outline: {title}

## Slide 1: Title
- {title}
- Authors: {authors}
- Institution, guide, and presentation date

## Slide 2: Background and Motivation
- Context and why the problem matters
- Current workflow limitations

## Slide 3: Problem Statement
- {problem}

## Slide 4: Objectives
{chr(10).join(f"- {objective}" for objective in objectives)}

## Slide 5: Existing vs Proposed System
- Existing approach and its limitations
- Proposed architecture and measurable improvement

## Slide 6: Technology Stack
- {technology_lines}
- Rationale for the selected technologies

## Slide 7: Methodology
- {methodology}
- Requirement, implementation, testing, and evaluation cycle

## Slide 8: System Architecture
- User interface
- Application services and data flow
- External integrations and security boundaries

## Slide 9: Demonstration and Results
- Key workflow demonstration
- Test evidence and performance observations

## Slide 10: Limitations and Future Scope
- Current constraints and threats to validity
- Planned improvements

## Slide 11: Conclusion
- Restate the contribution
- Map outcomes to objectives

## Slide 12: Viva Questions
- Why was this methodology selected?
- How were security and reliability validated?
- What are the main limitations and next steps?
"""

    if generation_mode == "user_based" and custom_outline.strip():
        chapter_titles = [line.strip().lstrip("-#0123456789. ").strip() for line in custom_outline.splitlines() if line.strip()]
    else:
        chapter_titles = [
            "Introduction",
            "Literature Review",
            "System Architecture",
            "Implementation",
            "Results and Discussion",
            "Conclusion and Future Work",
        ]

    chapter_sections: list[str] = []
    for number, chapter_title in enumerate(chapter_titles, start=1):
        normalized_title = chapter_title or f"Chapter {number}"
        if normalized_title.lower() == "introduction":
            body = f"This chapter introduces **{title}**, the problem it addresses, its motivation, scope, and objectives. The central problem is: {problem}"
        elif normalized_title.lower() == "literature review":
            body = f"This chapter reviews relevant approaches, tools, and research themes related to {technology_lines}. It identifies gaps in existing solutions and explains how the proposed work addresses those gaps."
        elif normalized_title.lower() == "system architecture":
            body = f"The proposed system is organized around {technology_lines}. Its major concerns are the user workflow, application services, persistence, security boundaries, and observable integrations."
        elif normalized_title.lower() == "implementation":
            body = f"This chapter describes the implementation strategy based on {methodology}. The implementation prioritizes modular interfaces, input validation, testability, and reproducible configuration."
        elif normalized_title.lower() in {"results", "results and discussion"}:
            body = "Results should report the selected evaluation metrics, test evidence, observed outcomes, comparison with the baseline, and threats to validity. Replace this planning text with measured project data."
        elif normalized_title.lower() in {"conclusion", "conclusion and future work"}:
            body = f"The project addresses the stated objectives for **{title}**. Future work should validate the solution with broader data, real users, and longer-running production-like experiments."
        else:
            body = f"This chapter focuses on the requested area **{normalized_title}** in the context of **{title}**. Document the relevant design decisions, evidence, implementation details, and project-specific findings here."
        chapter_sections.append(f"## Chapter {number}: {normalized_title}\n\n{body}")

    mode_label = "Automatic AI Structured" if generation_mode == "auto" else "User-Based Custom Outline"
    thesis = f"""# Project Report / Thesis: {title}

**Prepared by:** {authors}  
**Generation mode:** {mode_label}  
**Methodology:** {methodology}

## Abstract

This project report presents **{title}**, developed to address the following problem: {problem} The solution uses {technology_lines} and is evaluated against its objectives, quality attributes, and documented limitations.

## Objectives

{objective_lines}

{chr(10).join(chapter_sections)}

## References and Appendices

- Add verified academic references, datasets, configuration listings, test cases, and supplementary evidence.
- Replace planning language with project-specific measurements before submission.
"""
    return {"srs_markdown": srs, "research_paper_markdown": research, "slides_markdown": slides, "project_report_markdown": thesis}