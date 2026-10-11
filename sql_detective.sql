-- ============================================================================
-- SQL DETECTIVE CHALLENGE
-- Database schema: recruiters, job_postings, applicants, interviews
-- ============================================================================

-- Question 1
-- List all currently open job postings, along with the name of the recruiter who owns each one.
SELECT 
    jp.id AS job_posting_id,
    jp.title,
    jp.department,
    jp.opened_date,
    jp.status,
    r.name AS recruiter_name
FROM job_postings jp
JOIN recruiters r ON jp.recruiter_id = r.id
WHERE jp.status = 'open';


-- Question 2
-- For each job posting, how many applicants reached the Final interview stage?
-- Includes postings with zero Final-stage applicants using an outer join.
SELECT 
    jp.id AS job_posting_id,
    jp.title,
    COUNT(DISTINCT i.applicant_id) AS final_stage_applicants_count
FROM job_postings jp
LEFT JOIN interviews i 
    ON jp.id = i.job_posting_id 
   AND i.stage = 'Final'
GROUP BY jp.id, jp.title;


-- Question 3
-- Find every person who effectively applied to more than one job posting.
-- Normalizes email addresses to handle case variations (e.g. duplicate Ananya Rao records)
-- and counts distinct job postings reached through interviews.
SELECT 
    LOWER(a.email) AS normalized_email,
    MAX(a.full_name) AS applicant_name,
    COUNT(DISTINCT i.job_posting_id) AS distinct_job_postings_count
FROM applicants a
JOIN interviews i ON a.id = i.applicant_id
GROUP BY LOWER(a.email)
HAVING COUNT(DISTINCT i.job_posting_id) > 1;


-- Question 4
-- For each recruiter, compute their Final-stage conversion rate (passed ÷ total Final-stage interviews),
-- filtered to recruiters with at least 3 Final-stage interviews. Safe division handled via NULLIF.
SELECT 
    r.id AS recruiter_id,
    r.name AS recruiter_name,
    COUNT(i.id) AS total_final_interviews,
    SUM(CASE WHEN i.outcome = 'passed' THEN 1 ELSE 0 END) AS passed_final_interviews,
    ROUND(1.0 * SUM(CASE WHEN i.outcome = 'passed' THEN 1 ELSE 0 END) / NULLIF(COUNT(i.id), 0), 4) AS conversion_rate
FROM recruiters r
JOIN job_postings jp ON r.id = jp.recruiter_id
JOIN interviews i ON jp.id = i.job_posting_id
WHERE i.stage = 'Final'
GROUP BY r.id, r.name
HAVING COUNT(i.id) >= 3;


-- Question 5 (Bonus)
-- Using a window function, find the recruiter with the most successful placements (passed at Final stage)
-- per department, including recruiters/departments with zero placements. Uses DENSE_RANK() to retain ties.
WITH successful_placements AS (
    SELECT DISTINCT applicant_id, job_posting_id
    FROM interviews
    WHERE stage = 'Final' AND outcome = 'passed'
),
department_recruiter_placements AS (
    SELECT 
        jp.department,
        r.id AS recruiter_id,
        r.name AS recruiter_name,
        COUNT(sp.applicant_id) AS successful_placements,
        DENSE_RANK() OVER (
            PARTITION BY jp.department 
            ORDER BY COUNT(sp.applicant_id) DESC
        ) AS rank_in_department
    FROM job_postings jp
    JOIN recruiters r ON r.id = jp.recruiter_id
    LEFT JOIN successful_placements sp ON sp.job_posting_id = jp.id
    GROUP BY jp.department, r.id, r.name
)
SELECT 
    department,
    recruiter_id,
    recruiter_name,
    successful_placements
FROM department_recruiter_placements
WHERE rank_in_department = 1;
