/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CheckpointApprove } from '../models/CheckpointApprove';
import type { CheckpointListResponse } from '../models/CheckpointListResponse';
import type { CheckpointReject } from '../models/CheckpointReject';
import type { CheckpointResponse } from '../models/CheckpointResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class CheckpointService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * ??��������????????1?��???��??1
     * ��?��?????????????????1????��???��??1???��?��
     * @param executionId
     * @returns CheckpointListResponse Successful Response
     * @throws ApiError
     */
    public listPendingCheckpointsApiCheckpointsGet(
        executionId?: (string | null),
    ): CancelablePromise<CheckpointListResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/checkpoints',
            query: {
                'execution_id': executionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ��?��????��???��??1����|???
     * ��?��???????????�쨨????-??1???��????��????��???��??1?????��
     * @param executionId
     * @param stageId
     * @returns CheckpointResponse Successful Response
     * @throws ApiError
     */
    public getCheckpointApiCheckpointsExecutionIdStageIdGet(
        executionId: string,
        stageId: string,
    ): CancelablePromise<CheckpointResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/checkpoints/{execution_id}/{stage_id}',
            path: {
                'execution_id': executionId,
                'stage_id': stageId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ??1????��???��??1
     * ??1????��???��??1??��??��??-?��??���?o???�쨨??
     * @param executionId
     * @param stageId
     * @param requestBody
     * @returns CheckpointResponse Successful Response
     * @throws ApiError
     */
    public approveCheckpointApiCheckpointsExecutionIdStageIdApprovePost(
        executionId: string,
        stageId: string,
        requestBody: CheckpointApprove,
    ): CancelablePromise<CheckpointResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/checkpoints/{execution_id}/{stage_id}/approve',
            path: {
                'execution_id': executionId,
                'stage_id': stageId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ???????��???��??1
     * ???????��???��??1?1?����|?????????
     * @param executionId
     * @param stageId
     * @param requestBody
     * @returns CheckpointResponse Successful Response
     * @throws ApiError
     */
    public rejectCheckpointApiCheckpointsExecutionIdStageIdRejectPost(
        executionId: string,
        stageId: string,
        requestBody: CheckpointReject,
    ): CancelablePromise<CheckpointResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/checkpoints/{execution_id}/{stage_id}/reject',
            path: {
                'execution_id': executionId,
                'stage_id': stageId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ��?��????��???��??1?��????
     * ��?��???????????�쨨????????????��???��??1?��?????????��
     * @param executionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public getCheckpointSummaryApiCheckpointsExecutionIdSummaryGet(
        executionId: string,
    ): CancelablePromise<Record<string, any>> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/checkpoints/{execution_id}/summary',
            path: {
                'execution_id': executionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
