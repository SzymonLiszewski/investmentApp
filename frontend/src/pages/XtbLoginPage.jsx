import XtbLogin from "../components/login/XtbLogin";

function XtbLoginPage(){
    return (
        <div>
          <p> Note: Currently, this feature only supports XTB demo accounts. The functionality is under development, so errors or incomplete features may occur.</p>
          <XtbLogin />
        </div>
      );
}

export default XtbLoginPage;