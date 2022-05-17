module(...,package.seeall)

local tools = {}

function toolslist()
    for name, tool in pairs(tools) do
        if tool.references > 0 then
            item = "\\item[" .. name .. "] " .. tool.description 
            if tool.link then
                item = item .. "\\footnote{\\url{" .. tool.link .. "}}"
            end
            tex.print(item)
            tex.print("\\toolslabeltext{" .. name .. "}{" .. name .. "}")
        end
    end
end

function reftool(name)
    tools[name].references = tools[name].references+ 1
end

function declaretool(name, description, link)
    tools[name] = { 
        description = description, 
        link = link,
        references = 0
    }
end
