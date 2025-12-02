# Summary of Changes in Software Submission Guidelines (Version 2.0)

## 1. Executive Summary: Core Philosophy Change

The updated guidelines (Version 2.0) introduce a major shift in project evaluation. The focus is now on a hybrid assessment that combines academic rigor with professional software engineering practices.

**Key Change:** A new grading weight has been explicitly defined.
- **New Requirement:** Project evaluation is now a weighted combination:
  - **60% Academic & Research Criteria** (covered in the original guidelines, e.g., analysis, literature review).
  - **40% Technical Implementation Criteria** (covered by the new sections below).

This means the technical quality of the code is no longer just a foundation but a significant, graded part of the submission.

---

## 2. New Technical Chapters & Requirements

Three major chapters have been added, introducing new, mandatory technical requirements.

### 2.1. NEW SECTION: Chapter 15 - Project Organization as a Package

This section formalizes the requirement to structure the project as a professional, installable Python package.

- **New Requirement: Package Definition File**
  - The project **must** include a `pyproject.toml` or `setup.py` file.
  - This file must define the package's name, version, author, license, and a complete list of dependencies with specific version numbers or ranges.

- **New Requirement: `__init__.py` Files**
  - Every directory and subdirectory within the source code that is part of the package **must** contain an `__init__.py` file.
  - This file can be used to export public interfaces (using `__all__`) or define package-level variables like `__version__`.

- **New Requirement: Standardized Directory Structure**
  - Source code **must** be located in a dedicated directory (e.g., `src/` or a directory named after the package).
  - Tests **must** be in a separate `tests/` directory.
  - Documentation **must** be in a separate `docs/` directory.

- **New Requirement: Relative Imports**
  - All imports within the package code **must** be relative (e.g., `from . import utils`) or absolute from the package root (e.g., `from mypackage import utils`).
  - Code **must not** use absolute filesystem paths or manipulate `sys.path`.

### 2.2. NEW SECTION: Chapter 16 - Parallel Processing and Performance

This section requires a deliberate and correct implementation of concurrency to optimize performance.

- **New Requirement: Correct Choice of Concurrency Model**
  - **`multiprocessing`** must be used for CPU-bound tasks (e.g., complex calculations, data processing).
  - **`multithreading`** must be used for I/O-bound tasks (e.g., network requests, file I/O).
  - The project must justify the choice of concurrency model.

- **New Requirement: Thread/Process Safety**
  - When using `multithreading`, any shared data or variables **must** be protected using `locks`, `semaphores`, or other synchronization primitives to prevent race conditions.
  - When using `multiprocessing`, data must be shared safely between processes using `Queue` or `Pipe`.

- **New Requirement: Resource Management**
  - All threads and processes must be closed gracefully.
  - The number of processes should be determined dynamically (e.g., using `multiprocessing.cpu_count()`).

### 2.3. NEW SECTION: Chapter 17 - Modular Design and Building Blocks

This section mandates a modular architecture where the system is composed of independent, reusable "building blocks".

- **New Requirement: Formal "Building Block" Structure**
  - Each major component (or "building block") **must** be designed as a self-contained unit (e.g., a class).
  - Each block must have clearly defined inputs, outputs, and configuration parameters (`Input Data`, `Output Data`, `Setup Data`).

- **New Requirement: Adherence to Design Principles**
  - **Single Responsibility:** Each building block must be responsible for only one specific task.
  - **Separation of Concerns:** A block that performs calculations should not also be responsible for writing its results to disk.
  - **Reusability & Testability:** Each block must be designed to be testable in isolation and reusable in different contexts, with dependencies provided via dependency injection.

- **New Requirement: Input Validation**
  - Each building block **must** perform validation on its input data and fail fast with a clear error message if the input is invalid.

---

## 3. Modified Sections & Requirements

### 3.1. CHANGED SECTION: Chapter 13 - Final Checklist

The final checklist has been significantly expanded into a "Detailed Technical Check".

- **New Requirement:** The checklist now includes specific items to verify compliance with the new technical chapters (15, 16, and 17). This includes checking for:
  - The presence and correctness of `pyproject.toml`.
  - The use of `__init__.py` files.
  - The correct use of `multiprocessing` vs. `multithreading`.
  - The modular "building block" design.
  - Comprehensive validation of all inputs.
  - Detailed documentation for each building block.

---

## 4. Summary of Minor Structural Changes

- **New Chapter 1:** A new introduction, "New in Version 2.0," has been added, which summarizes the major changes.
- **Chapter Renumbering:** All original chapters have been renumbered to accommodate the new sections.
- **Document Versioning:** The document is now explicitly versioned as "2.0" with a new date of "22-11-2025".
