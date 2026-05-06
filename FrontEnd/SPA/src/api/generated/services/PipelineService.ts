/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DefaultPipelineResponse } from '../models/DefaultPipelineResponse';
import type { PipelineConfigResponse } from '../models/PipelineConfigResponse';
import type { PipelineCreate } from '../models/PipelineCreate';
import type { PipelineListResponse } from '../models/PipelineListResponse';
import type { PipelineResponse } from '../models/PipelineResponse';
import type { PipelineUpdate } from '../models/PipelineUpdate';
import type { SetDefaultPipelineRequest } from '../models/SetDefaultPipelineRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class PipelineService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * ?????o?��??���?o?
     * ?????o?????a??��????��??���?o????????1???�쨨???��??��????��????��
     * @param requestBody
     * @returns PipelineResponse Successful Response
     * @throws ApiError
     */
    public createPipelineApiPipelinesPost(
        requestBody: PipelineCreate,
    ): CancelablePromise<PipelineResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/pipelines',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ??��������?��??���?o????��?��
     * ???��?��??��������???????��??���?o?
     * @param page ��?��???
     * @param pageSize ?��?��?��??�㨦??
     * @returns PipelineListResponse Successful Response
     * @throws ApiError
     */
    public listPipelinesApiPipelinesGet(
        page: number = 1,
        pageSize: number = 20,
    ): CancelablePromise<PipelineListResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/pipelines',
            query: {
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ��?��????��??���?o?��?????
     * ??1???ID��?��??????????��??���?o????��??????????��
     * @param pipelineId
     * @returns PipelineConfigResponse Successful Response
     * @throws ApiError
     */
    public getPipelineApiPipelinesPipelineIdGet(
        pipelineId: string,
    ): CancelablePromise<PipelineConfigResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/pipelines/{pipeline_id}',
            path: {
                'pipeline_id': pipelineId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ??��??��?��??���?o?
     * ??��??��???????��??���?o????��?????
     * @param pipelineId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public updatePipelineApiPipelinesPipelineIdPut(
        pipelineId: string,
        requestBody: PipelineUpdate,
    ): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'PUT',
            url: '/api/pipelines/{pipeline_id}',
            path: {
                'pipeline_id': pipelineId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ???��?��?��??���?o?
     * ???��?��???????��??���?o?
     * @param pipelineId
     * @returns void
     * @throws ApiError
     */
    public deletePipelineApiPipelinesPipelineIdDelete(
        pipelineId: string,
    ): CancelablePromise<void> {
        return this.httpRequest.request({
            method: 'DELETE',
            url: '/api/pipelines/{pipeline_id}',
            path: {
                'pipeline_id': pipelineId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * ��?��???��??��?��?��??���?o?
     * ��?��?????????��???????o��??��?��????��??���?o??????��
     * @returns DefaultPipelineResponse Successful Response
     * @throws ApiError
     */
    public getDefaultPipelineApiPipelinesDefaultGet(): CancelablePromise<DefaultPipelineResponse> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/pipelines/default',
        });
    }
    /**
     * ��?????��??��?��?��??���?o?
     * ?��????????��??���?o?��???????o��??��?��?��??���?o?
     * @param requestBody
     * @returns DefaultPipelineResponse Successful Response
     * @throws ApiError
     */
    public setDefaultPipelineApiPipelinesDefaultPost(
        requestBody: SetDefaultPipelineRequest,
    ): CancelablePromise<DefaultPipelineResponse> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/pipelines/default',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
