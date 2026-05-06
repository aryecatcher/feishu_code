/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BaseHttpRequest } from './core/BaseHttpRequest';
import type { OpenAPIConfig } from './core/OpenAPI';
import { AxiosHttpRequest } from './core/AxiosHttpRequest';
import { CheckpointService } from './services/CheckpointService';
import { ExecutionService } from './services/ExecutionService';
import { HealthService } from './services/HealthService';
import { PipelineService } from './services/PipelineService';
import { RootService } from './services/RootService';
type HttpRequestConstructor = new (config: OpenAPIConfig) => BaseHttpRequest;
export class ApiClient {
    public readonly checkpoint: CheckpointService;
    public readonly execution: ExecutionService;
    public readonly health: HealthService;
    public readonly pipeline: PipelineService;
    public readonly root: RootService;
    public readonly request: BaseHttpRequest;
    constructor(config?: Partial<OpenAPIConfig>, HttpRequest: HttpRequestConstructor = AxiosHttpRequest) {
        this.request = new HttpRequest({
            BASE: config?.BASE ?? '',
            VERSION: config?.VERSION ?? '0.1.0',
            WITH_CREDENTIALS: config?.WITH_CREDENTIALS ?? false,
            CREDENTIALS: config?.CREDENTIALS ?? 'include',
            TOKEN: config?.TOKEN,
            USERNAME: config?.USERNAME,
            PASSWORD: config?.PASSWORD,
            HEADERS: config?.HEADERS,
            ENCODE_PATH: config?.ENCODE_PATH,
        });
        this.checkpoint = new CheckpointService(this.request);
        this.execution = new ExecutionService(this.request);
        this.health = new HealthService(this.request);
        this.pipeline = new PipelineService(this.request);
        this.root = new RootService(this.request);
    }
}

