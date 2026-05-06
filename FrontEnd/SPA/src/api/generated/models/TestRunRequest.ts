/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request for test-run endpoint.
 */
export type TestRunRequest = {
    /**
     * Pipeline ID to execute
     */
    pipeline_id: string;
    /**
     * Demand/requirement description
     */
    demand: string;
    /**
     * Output directory for generated files
     */
    output_dir?: string;
};

