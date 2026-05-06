/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExecutionCreate } from '../models/ExecutionCreate';
import type { ExecutionResponse } from '../models/ExecutionResponse';
import type { ExecutionStatusResponse } from '../models/ExecutionStatusResponse';
import type { TestRunRequest } from '../models/TestRunRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class ExecutionService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * ?????o?1???��??��??�쨨??
     * ?????o??��?????�쨨?????????1?????-��??��??��?��??���?o?
     * @param requestBody
     * @returns ExecutionResponse Successful Response
     * @throws ApiError
     */
    public createExecutionApiExecutionsPost(
        requestBody: ExecutionCreate,
    ): CancelablePromise<ExecutionResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/executions',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ??��������??�쨨?????��?��
     * ???��?��??��������??�쨨???????2��?��???
     * @param pipelineId ????��??���?o?ID?-?��??
     * @param page ��?��???
     * @param pageSize ?��?��?��??�㨦??
     * @returns any Successful Response
     * @throws ApiError
     */
    public listExecutionsApiExecutionsGet(
        pipelineId?: (string | null),
        page: number = 1,
        pageSize: number = 20,
    ): CancelablePromise<Record<string, any>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/executions',
            query: {
                'pipeline_id': pipelineId,
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ��?��?????�쨨??����|???
     * ??��???????????�쨨?????����|????????????��???o|
     * @param executionId
     * @returns ExecutionStatusResponse Successful Response
     * @throws ApiError
     */
    public getExecutionApiExecutionsExecutionIdGet(
        executionId: string,
    ): CancelablePromise<ExecutionStatusResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/executions/{execution_id}',
            path: {
                'execution_id': executionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ��?��?????�쨨????????
     * ��?��?????�쨨????????????????��??1???
     * @param executionId
     * @returns ExecutionStatusResponse Successful Response
     * @throws ApiError
     */
    public getExecutionStatusApiExecutionsExecutionIdStatusGet(
        executionId: string,
    ): CancelablePromise<ExecutionStatusResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/executions/{execution_id}/status',
            path: {
                'execution_id': executionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ????????�쨨??
     * ???????-��??����??��???????�쨨??
     * @param executionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public cancelExecutionApiExecutionsExecutionIdCancelPost(
        executionId: string,
    ): CancelablePromise<Record<string, any>> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/executions/{execution_id}/cancel',
            path: {
                'execution_id': executionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ????????�쨨??
     * ???????-��??����??��???????�쨨??
     * @param executionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public pauseExecutionApiExecutionsExecutionIdPausePost(
        executionId: string,
    ): CancelablePromise<Record<string, any>> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/executions/{execution_id}/pause',
            path: {
                'execution_id': executionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ??��?��???�쨨??
     * ?????????????????��?��???�쨨??
     * @param executionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public resumeExecutionApiExecutionsExecutionIdResumePost(
        executionId: string,
    ): CancelablePromise<Record<string, any>> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/executions/{execution_id}/resume',
            path: {
                'execution_id': executionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ?��?����?��??��???��??���?o?
     * ??��??��?��?����??��??���?o???�쨨?????????-��??????��?a??��?��????????????��??????????????��????????????
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public testRunPipelineApiExecutionsTestRunPost(
        requestBody: TestRunRequest,
    ): CancelablePromise<Record<string, any>> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/executions/test-run',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
