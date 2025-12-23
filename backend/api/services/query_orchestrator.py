"""
Query Orchestrator for Multi-Step Analysis

Coordinates the multi-step process of analyzing questions, generating queries,
executing them, and providing data-driven answers.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from .llm_base import BaseLLMService
from .prompts import (
    build_planning_prompt,
    build_query_generation_prompt,
    build_analysis_prompt,
    build_error_correction_prompt
)
from ..utils.sql_executor import SafeSQLExecutor
from ..utils.sql_cleaner import clean_sql_query

logger = logging.getLogger(__name__)


class QueryOrchestrator:
    """
    Orchestrates multi-step query analysis and execution.

    Process:
    1. Planning: Analyze question and determine data needs
    2. Query Generation: Create SQL queries based on plan
    3. Execution: Execute queries and gather results
    4. Analysis: Analyze results and generate final answer
    """

    MAX_QUERIES_PER_QUESTION = 5

    def __init__(
        self,
        llm_service: BaseLLMService,
        sql_executor: SafeSQLExecutor,
        db_type: str,
        schema: dict,
        allowed_tables: list
    ):
        """
        Initialize the orchestrator.

        Args:
            llm_service: The LLM service to use for generation
            sql_executor: SQL executor for running queries
            db_type: Database type (postgresql, mysql, sqlite, etc.)
            schema: Database schema dictionary
            allowed_tables: List of tables the user can access
        """
        self.llm_service = llm_service
        self.sql_executor = sql_executor
        self.db_type = db_type
        self.schema = schema
        self.allowed_tables = allowed_tables

    def execute(self, question: str) -> Dict[str, Any]:
        """
        Execute the full multi-step analysis process.

        Args:
            question: User's natural language question

        Returns:
            Dictionary containing:
                - answer: The final answer to the question
                - explanation: Brief explanation
                - insights: Key insights from the data
                - representative_sql: SQL query for display
                - chart_type: Suggested chart type
                - chart_config: Chart configuration
                - results: Combined query results
                - intermediate_queries: List of executed queries
                - reasoning_steps: JSON of intermediate steps
        """
        try:
            # Phase 1: Planning
            logger.info("Phase 1: Planning - Analyzing question")
            plan = self._phase_1_planning(question)

            # Phase 2: Query Generation
            logger.info("Phase 2: Query Generation - Creating SQL queries")
            queries = self._phase_2_query_generation(plan)

            # Phase 3: Execution
            logger.info("Phase 3: Execution - Running queries")
            results, intermediate_queries = self._phase_3_execution(queries)

            # Phase 4: Analysis
            logger.info("Phase 4: Analysis - Generating final answer")
            analysis = self._phase_4_analysis(question, results, len(queries))

            # Combine results
            return {
                'answer': analysis.get('answer', ''),
                'explanation': analysis.get('explanation', ''),
                'insights': analysis.get('insights', ''),
                'representative_sql': analysis.get('representative_sql', ''),
                'chart_type': analysis.get('chart_suggestion', {}).get('type', 'none'),
                'chart_config': analysis.get('chart_suggestion', {}),
                'results': self._combine_results(results),
                'intermediate_queries': intermediate_queries,
                'reasoning_steps': json.dumps({
                    'plan': plan,
                    'query_count': len(queries),
                    'data_summary': analysis.get('data_summary', '')
                })
            }

        except Exception as e:
            logger.error(f"Error in query orchestration: {str(e)}")
            raise

    def _phase_1_planning(self, question: str) -> Dict[str, Any]:
        """
        Phase 1: Analyze the question and create a data gathering plan.

        Args:
            question: User's question

        Returns:
            Planning dictionary with understanding, data_needs, and query_plan
        """
        prompt = build_planning_prompt(
            question=question,
            db_type=self.db_type,
            schema=self.schema,
            allowed_tables=self.allowed_tables
        )

        response = self.llm_service.generate(
            system_prompt="You are an expert data analyst creating data gathering plans.",
            user_prompt=prompt
        )

        # Parse JSON response
        plan = self._parse_json_response(response)
        logger.debug(f"Planning phase result: {plan}")

        return plan

    def _phase_2_query_generation(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Phase 2: Generate SQL queries based on the plan.

        Args:
            plan: The planning dictionary from Phase 1

        Returns:
            List of query dictionaries with query_id, sql, purpose, expected_columns
        """
        prompt = build_query_generation_prompt(
            plan=json.dumps(plan, indent=2),
            db_type=self.db_type,
            schema=self.schema,
            allowed_tables=self.allowed_tables
        )

        response = self.llm_service.generate(
            system_prompt="You are an expert SQL developer generating optimized queries.",
            user_prompt=prompt
        )

        # Parse JSON response
        query_response = self._parse_json_response(response)
        queries = query_response.get('queries', [])

        # Validate query count
        if len(queries) > self.MAX_QUERIES_PER_QUESTION:
            logger.warning(f"Too many queries generated ({len(queries)}), truncating to {self.MAX_QUERIES_PER_QUESTION}")
            queries = queries[:self.MAX_QUERIES_PER_QUESTION]

        if not queries:
            raise ValueError("No queries generated from plan")

        logger.debug(f"Generated {len(queries)} queries")
        return queries

    def _phase_3_execution(self, queries: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Phase 3: Execute the SQL queries and gather results.

        Args:
            queries: List of query dictionaries from Phase 2

        Returns:
            Tuple of (results_dict, intermediate_queries_list)
            - results_dict: Maps query_id to execution results
            - intermediate_queries_list: List of executed queries with metadata
        """
        results = {}
        intermediate_queries = []

        for query_info in queries:
            query_id = query_info.get('query_id', f"query_{len(results) + 1}")
            sql = query_info.get('sql', '')
            purpose = query_info.get('purpose', '')

            if not sql:
                logger.warning(f"Empty SQL for {query_id}, skipping")
                continue

            try:
                # Clean the SQL
                cleaned_sql = clean_sql_query(sql)

                # Execute the query
                success, query_results, message = self.sql_executor.execute(cleaned_sql)

                if not success:
                    raise Exception(message)

                # Store results
                results[query_id] = {
                    'sql': cleaned_sql,
                    'purpose': purpose,
                    'results': query_results or [],
                    'row_count': len(query_results) if query_results else 0,
                    'success': True
                }

                # Track intermediate query
                intermediate_queries.append({
                    'query_id': query_id,
                    'sql': cleaned_sql,
                    'purpose': purpose,
                    'row_count': len(query_results) if query_results else 0,
                    'success': True
                })

                logger.info(f"Executed {query_id}: {len(query_results) if query_results else 0} rows returned")

            except Exception as e:
                logger.error(f"Error executing {query_id}: {str(e)}")

                # Try to fix the query once
                try:
                    fixed_sql = self._attempt_query_fix(sql, str(e))
                    if fixed_sql:
                        cleaned_sql = clean_sql_query(fixed_sql)
                        success, query_results, message = self.sql_executor.execute(cleaned_sql)

                        if not success:
                            raise Exception(message)

                        results[query_id] = {
                            'sql': cleaned_sql,
                            'purpose': purpose,
                            'results': query_results or [],
                            'row_count': len(query_results) if query_results else 0,
                            'success': True,
                            'fixed': True
                        }

                        intermediate_queries.append({
                            'query_id': query_id,
                            'sql': cleaned_sql,
                            'purpose': purpose,
                            'row_count': len(query_results) if query_results else 0,
                            'success': True,
                            'fixed': True
                        })

                        logger.info(f"Fixed and executed {query_id}: {len(query_results) if query_results else 0} rows returned")
                    else:
                        raise

                except Exception as retry_error:
                    # Store error information
                    results[query_id] = {
                        'sql': sql,
                        'purpose': purpose,
                        'results': [],
                        'row_count': 0,
                        'success': False,
                        'error': str(retry_error)
                    }

                    intermediate_queries.append({
                        'query_id': query_id,
                        'sql': sql,
                        'purpose': purpose,
                        'row_count': 0,
                        'success': False,
                        'error': str(retry_error)
                    })

                    logger.error(f"Failed to fix {query_id}, continuing with other queries")

        return results, intermediate_queries

    def _phase_4_analysis(
        self,
        question: str,
        results: Dict[str, Any],
        query_count: int
    ) -> Dict[str, Any]:
        """
        Phase 4: Analyze the results and generate the final answer.

        Args:
            question: Original user question
            results: Dictionary of query results from Phase 3
            query_count: Number of queries that were attempted

        Returns:
            Analysis dictionary with answer, explanation, insights, representative_sql, chart_suggestion
        """
        # Calculate statistics
        non_empty_count = sum(1 for r in results.values() if r.get('success') and r.get('row_count', 0) > 0)
        total_rows = sum(r.get('row_count', 0) for r in results.values() if r.get('success'))

        # Format results for the LLM
        formatted_results = self._format_results_for_analysis(results)

        prompt = build_analysis_prompt(
            question=question,
            results=formatted_results,
            query_count=query_count,
            non_empty_count=non_empty_count,
            total_rows=total_rows
        )

        response = self.llm_service.generate(
            system_prompt="You are an expert data analyst providing insights from query results.",
            user_prompt=prompt
        )

        # Parse JSON response
        analysis = self._parse_json_response(response)
        logger.debug(f"Analysis phase result: {analysis}")

        return analysis

    def _attempt_query_fix(self, sql: str, error: str) -> Optional[str]:
        """
        Attempt to fix a failed SQL query using the error correction prompt.

        Args:
            sql: The SQL that failed
            error: The error message

        Returns:
            Fixed SQL string or None if fix failed
        """
        try:
            prompt = build_error_correction_prompt(
                error=error,
                previous_sql=sql,
                db_type=self.db_type
            )

            response = self.llm_service.generate(
                system_prompt="You are an expert SQL developer fixing query errors.",
                user_prompt=prompt
            )

            # Parse JSON response
            fixed_response = self._parse_json_response(response)
            fixed_sql = fixed_response.get('sql', '')

            if fixed_sql and fixed_sql != sql:
                logger.info("Successfully generated fixed SQL")
                return fixed_sql

            return None

        except Exception as e:
            logger.error(f"Error attempting to fix query: {str(e)}")
            return None

    def _format_results_for_analysis(self, results: Dict[str, Any]) -> str:
        """
        Format query results for the analysis prompt.

        Args:
            results: Dictionary of query results

        Returns:
            Formatted string representation of results
        """
        formatted = []

        for query_id, result_info in results.items():
            formatted.append(f"\n{query_id.upper()}:")
            formatted.append(f"  Purpose: {result_info.get('purpose', 'N/A')}")
            formatted.append(f"  Success: {result_info.get('success', False)}")
            formatted.append(f"  Rows: {result_info.get('row_count', 0)}")

            if result_info.get('success'):
                query_results = result_info.get('results', [])
                if query_results:
                    # Show first few rows
                    formatted.append(f"  Sample Data (first 5 rows):")
                    for i, row in enumerate(query_results[:5]):
                        formatted.append(f"    Row {i+1}: {json.dumps(row)}")

                    if len(query_results) > 5:
                        formatted.append(f"    ... and {len(query_results) - 5} more rows")
                else:
                    formatted.append("  No data returned")
            else:
                formatted.append(f"  Error: {result_info.get('error', 'Unknown error')}")

            formatted.append("")

        return '\n'.join(formatted)

    def _combine_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Combine results from multiple queries into a single list.

        For now, we return the results from the last successful query.
        In the future, this could be smarter about combining data.

        Args:
            results: Dictionary of query results

        Returns:
            Combined list of result rows
        """
        # Find the last successful query with data
        for query_id in reversed(list(results.keys())):
            result_info = results[query_id]
            if result_info.get('success') and result_info.get('row_count', 0) > 0:
                return result_info.get('results', [])

        # No successful queries with data
        return []

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks.

        Args:
            response: Raw LLM response

        Returns:
            Parsed JSON dictionary
        """
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response was: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
