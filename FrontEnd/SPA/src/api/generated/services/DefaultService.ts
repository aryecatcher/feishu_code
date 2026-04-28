/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Checkpoint } from '../models/Checkpoint';
import type { PipelineConfig } from '../models/PipelineConfig';
import type { RunSummary } from '../models/RunSummary';
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class DefaultService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * 获取流水线详情
     * 获取流水线模板详情信息。
     * @param pipelineId
     * @returns PipelineConfig
     * @throws ApiError
     */
    public getApiV1Pipelines(
        pipelineId: string,
    ): CancelablePromise<PipelineConfig> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/v1/pipelines/{pipeline_id}',
            path: {
                'pipeline_id': pipelineId,
            },
        });
    }
    /**
     * 更新流水线定义
     * 更新流水线模板信息。
     * @param pipelineId
     * @returns any
     * @throws ApiError
     */
    public putApiV1Pipelines(
        pipelineId: string,
    ): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'PUT',
            url: '/api/v1/pipelines/{pipeline_id}',
            path: {
                'pipeline_id': pipelineId,
            },
        });
    }
    /**
     * 创建并运行流水线实例
     * 基于定义创建并运行流水线实例，返回运行实例ID。
     * @param pipelineId
     * @returns RunSummary
     * @throws ApiError
     */
    public postApiV1PipelinesRun(
        pipelineId: string,
    ): CancelablePromise<RunSummary> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/v1/pipelines/{pipeline_id}/run',
            path: {
                'pipeline_id': pipelineId,
            },
        });
    }
    /**
     * 获取检查点列表
     * 获取检查点的概述信息
     * @param runId
     * @returns Checkpoint
     * @throws ApiError
     */
    public getApiRunsCheckpoints(
        runId: string,
    ): CancelablePromise<Checkpoint> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/runs/{run_id}/checkpoints',
            path: {
                'run_id': runId,
            },
        });
    }
    /**
     * 获取检查点详情
     * @param runId
     * @param stageId
     * @returns any
     * @throws ApiError
     */
    public getApiRuns(
        runId: string,
        stageId: string,
    ): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/runs/{run_id}/{stage_id}',
            path: {
                'run_id': runId,
                'stage_id': stageId,
            },
        });
    }
    /**
     * 通过检查点
     * 通过该检查点
     * @param runId
     * @param stageId
     * @returns any
     * @throws ApiError
     */
    public postApiRunsApprove(
        runId: string,
        stageId: string,
    ): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/runs/{run_id}/{stage_id}/approve',
            path: {
                'run_id': runId,
                'stage_id': stageId,
            },
        });
    }
    /**
     * 驳回检查点
     * 驳回该检查点
     * @param runId
     * @param stageId
     * @returns any
     * @throws ApiError
     */
    public postApiRunsReject(
        runId: string,
        stageId: string,
    ): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/runs/{run_id}/{stage_id}/reject',
            path: {
                'run_id': runId,
                'stage_id': stageId,
            },
        });
    }
    /**
     * 获取实例详情
     * 获取实例运行摘要信息
     * @param runId 唯一实例ID
     * @returns RunSummary
     * @throws ApiError
     */
    public getApiRuns1(
        runId: string,
    ): CancelablePromise<RunSummary> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/api/runs/{run_id}',
            path: {
                'run_id': runId,
            },
        });
    }
    /**
     * 暂停执行
     * 暂停实例执行
     * @param runId
     * @returns any
     * @throws ApiError
     */
    public postApiRunsPause(
        runId: string,
    ): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/runs/{run_id}/pause',
            path: {
                'run_id': runId,
            },
        });
    }
    /**
     * 恢复执行
     * 恢复暂停的实例执行
     * @param runId
     * @returns any
     * @throws ApiError
     */
    public postApiRunsResume(
        runId: string,
    ): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/runs/{run_id}/resume',
            path: {
                'run_id': runId,
            },
        });
    }
    /**
     * 强制终止
     * 强制停止进行中的实例执行
     * @param runId
     * @returns any
     * @throws ApiError
     */
    public postApiRunsTerminate(
        runId: string,
    ): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'POST',
            url: '/api/runs/{run_id}/terminate',
            path: {
                'run_id': runId,
            },
        });
    }
}
