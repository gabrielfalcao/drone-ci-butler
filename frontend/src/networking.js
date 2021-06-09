import axios, {
  AxiosRequestConfig,
  AxiosResponse,
  // AxiosPromise
} from "axios";
import { TermProps } from "./domain/terms";
import { UserProps } from "./domain/users";

export class APIRouter {
  constructor(baseURL) {
    const match = baseURL.match(/^(https?:[/][/].*)[/]+$/);
    if (!match) {
      throw new Error(`Invalid url: "${baseURL}"`);
    }
    this.baseURL = baseURL;
    console.log(`API Router base url= ${baseURL}`);
  }

  urlFor = (path) => {
    return [this.baseURL.replace(/[/]+$/, ""), path.replace(/^[/]+/, "")].join(
      "/"
    );
  };
}

const getAPIBaseURL = () => {
  // if ((window.location.href + "").match(/localhost/)) {
  //     return "http://localhost:5000/";
  // }
  return "https://drone-ci-butler.ngrok.io/";
};

export type ErrorHandler = (err) => void;
export type SuccessHandler = (data) => void;

export class CoreAPIClient {
  constructor(handleError: ErrorHandler) {
    this.api = new APIRouter(getAPIBaseURL());
    this.defaultOptions = {
      headers: {
        "Content-Type": "application/json",
      },
    };
    this.handleError = handleError;
  }

  setToken = (accessToken) => {
    this.defaultOptions.headers["Authorization"] = `Bearer ${accessToken}`;
  };
  getOptions = () => {
    return { ...this.defaultOptions };
  };
}

export class AuthAPIClient extends CoreAPIClient {
  authenticate = (email, password, handler): void => {
    const url = this.api.urlFor("/api/v1/auth/");
    axios
      .post(url, { email, password, scope: "admin" }, this.getOptions())
      .then((response) => {
        console.log("response", response);
        return response.data;
      })
      .catch(this.handleError)
      .then(handler);
  };
}

export class BaseAPIClient extends CoreAPIClient {
  constructor(handleError: ErrorHandler, token) {
    super(handleError);
    this.api = new APIRouter(getAPIBaseURL());
    this.defaultOptions = {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    };
  }
}

export class AdminAPIClient extends BaseAPIClient {
  listUsers = (handler): void => {
    const url = this.api.urlFor("/api/v1/users/");
    axios
      .get(url, this.getOptions())
      .then((response: AxiosResponse<UserProps[]>) => {
        return response.data;
      })
      .catch(this.handleError)
      .then(handler);
  };
  searchUser = (email, handler): void => {
    const url = this.api.urlFor(`/api/v1/users/by-email/?email=${email}`);
    axios
      .get(url, this.getOptions())
      .then((response) => {
        return response.data;
      })
      .catch(this.handleError)
      .then(handler);
  };
  deleteUser = (id, handler): void => {
    const url = this.api.urlFor(`/api/v1/users/${id}/`);
    axios
      .delete(url, this.getOptions())
      .then((response) => {
        return response.data;
      })
      .catch(this.handleError)
      .then(handler);
  };
  createUser = (email, password, handler): void => {
    const url = this.api.urlFor("/api/v1/users/");
    axios
      .post(url, { email, password }, this.getOptions())
      .then((response) => {
        return response.data;
      })
      .catch(this.handleError)
      .then(handler);
  };
}
