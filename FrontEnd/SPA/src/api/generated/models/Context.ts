/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Context = {
    /**
     * 绑定运行实例
     */
    run_id: number;
    /**
     * 标注交付内容
     */
    context_id: number;
    /**
     * initial|checkpoint
     */
    type: string;
    /**
     * 具体交付内容
     */
    content: {
        /**
         * 可选，提示词内容
         */
        prompt?: string;
        /**
         * 可选，上下文内容
         */
        refs?: {
            codebase?: any;
            dom?: any;
        };
    };
};

