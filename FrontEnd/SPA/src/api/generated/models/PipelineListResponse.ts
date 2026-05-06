/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PipelineResponse } from './PipelineResponse';
/**
 * List of pipelines.
 */
export type PipelineListResponse = {
    items: Array<PipelineResponse>;
    total: number;
    page: number;
    page_size: number;
};

