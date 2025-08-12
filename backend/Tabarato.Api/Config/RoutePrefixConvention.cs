using Microsoft.AspNetCore.Mvc.ApplicationModels;
using Microsoft.AspNetCore.Mvc.Routing;

namespace Tabarato.Api.Config;

public class RoutePrefixConvention(IRouteTemplateProvider route) : IApplicationModelConvention
{
    private readonly AttributeRouteModel _routePrefix = new(route);

    public void Apply(ApplicationModel application)
    {
        foreach (var controller in application.Controllers)
        {
            foreach (var selector in controller.Selectors)
            {
                if (selector.AttributeRouteModel != null)
                {
                    selector.AttributeRouteModel = AttributeRouteModel.CombineAttributeRouteModel(
                        _routePrefix,
                        selector.AttributeRouteModel);
                }
                else
                {
                    selector.AttributeRouteModel = _routePrefix;
                }
            }
        }
    }
}