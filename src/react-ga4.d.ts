declare module 'react-ga4' {
    export interface ReactGA4Options {
      gaOptions?: {
        [key: string]: any;
      };
      debug?: boolean;
      testMode?: boolean;
      gtagOptions?: {
        [key: string]: any;
      };
    }
  
    export function initialize(
      measurementId: string | string[],
      options?: ReactGA4Options
    ): void;
  
    export function send(
      params: {
        hitType: string;
        page: string;
      }
    ): void;
  
    export default {
      initialize,
      send
    };
  }