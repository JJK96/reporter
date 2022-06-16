module(...,package.seeall)

local tools = {}

function toolslist()
    local output = ""
    for name, tool in pairs(tools) do
        if tool.references > 0 then
            item = "\\item[" .. name .. "] " .. tool.description 
            if tool.link then
                item = item .. "\\footnote{\\url{" .. tool.link .. "}}"
            end
            output = output .. item .. "\\toolslabeltext{" .. name .. "}{" .. name .. "}"
        end
    end
    if not (output == "") then
        tex.print("\\toolslistheader")
        tex.print("\\begin{description}")
        tex.print(output)
        tex.print("\\end{description}")
    end
end

function reftool(name)
    if tools[name] == nil then
        tex.print("\\PackageError{tools}{The tool \"" .. name .. "\" is not defined}{The tool should be defined using \\declaretool}")
        return
    end
    tools[name].references = tools[name].references+ 1
end

function declaretool(name, description, link)
    tools[name] = { 
        description = description, 
        link = link,
        references = 0
    }
end
