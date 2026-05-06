/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import type { BaseHttpRequest } from '../core/BaseHttpRequest';
export class RootService {
    constructor(public readonly httpRequest: BaseHttpRequest) {}
    /**
     * Root
     * Root endpoint.
     * @returns any Successful Response
     * @throws ApiError
     */
    public rootGet(): CancelablePromise<any> {
        return this.httpRequest.request({
            method: 'GET',
            url: '/',
        });
    }
}
